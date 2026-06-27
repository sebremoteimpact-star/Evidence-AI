"""Caso de uso orquestador: ejecuta el pipeline completo de verificación.

Se invoca desde el worker arq (tarea `run_verification`).
Emite eventos en cada paso vía EventPublisher (alimenta SSE).

Pipeline:
  1. Ingestar (texto, URL, YouTube → texto canónico).
  2. Detectar manipulación (sobre el input original).
  3. Extraer claims atómicos.
  4. Para cada claim factual:
     a. Generar queries de búsqueda.
     b. Buscar evidencia (multi-proveedor).
     c. Fetch + extracción de pasajes.
     d. Razonar sobre evidencia con Claude.
  5. Calcular confianza por claim (determinista).
  6. Componer reporte.
  7. Persistir todo.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select

from evidence_ai.application.ports.ai_reasoner import AIReasoner
from evidence_ai.application.ports.content_fetcher import ContentFetcher, FetchedContent
from evidence_ai.application.ports.event_publisher import EventPublisher
from evidence_ai.application.ports.search_provider import SearchProvider, SearchQuery
from evidence_ai.config.source_registry import extract_domain, lookup
from evidence_ai.domain.services.confidence_calculator import (
    ConfidenceCalculator,
    EvidencePiece,
)
from evidence_ai.domain.value_objects import (
    ClaimType,
    InputType,
    Stance,
    Verdict,
    VerificationStatus,
)
from evidence_ai.infrastructure.persistence.models import (
    ClaimModel,
    EvidenceModel,
    ManipulationSignalModel,
    ReportModel,
    SourceModel,
    VerificationModel,
)
from evidence_ai.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

logger = structlog.get_logger(__name__)


class VerifyContentUseCase:
    """El monstruo. Orquesta todo el pipeline."""

    def __init__(
        self,
        uow_factory,  # callable: () -> SqlAlchemyUnitOfWork
        fetchers: list[ContentFetcher],
        search_providers: list[SearchProvider],
        ai_reasoner: AIReasoner,
        event_publisher: EventPublisher,
        confidence_calculator: ConfidenceCalculator,
        max_sources_per_claim: int = 10,
    ) -> None:
        self._uow_factory = uow_factory
        self._fetchers = fetchers
        self._search_providers = search_providers
        self._ai = ai_reasoner
        self._events = event_publisher
        self._calc = confidence_calculator
        self._max_sources = max_sources_per_claim

    async def execute(self, verification_id: UUID) -> None:
        logger.info("verify_pipeline_start", verification_id=str(verification_id))
        try:
            # ── Cargar la verificación ──
            uow = self._uow_factory()
            async with uow:
                result = await uow.session.execute(
                    select(VerificationModel).where(VerificationModel.id == verification_id)
                )
                verification = result.scalar_one()
                input_type = verification.input_type
                input_raw = verification.input_raw
                user_language_hint = verification.language

            # ── 1. Ingestar ──
            await self._set_status(verification_id, VerificationStatus.INGESTING)
            await self._emit(verification_id, "ingesting", {})
            normalized, source_url, language = await self._ingest(input_type, input_raw)

            uow = self._uow_factory()
            async with uow:
                v = (await uow.session.execute(
                    select(VerificationModel).where(VerificationModel.id == verification_id)
                )).scalar_one()
                v.input_normalized = normalized[:50000]
                v.source_url = source_url
                v.language = language or user_language_hint or "es"
                await uow.session.flush()
            language = language or "es"

            await self._emit(verification_id, "ingested", {
                "language": language,
                "chars": len(normalized),
                "source_url": source_url,
            })

            # ── 2. Detectar manipulación (paralelo con extracción) ──
            await self._set_status(verification_id, VerificationStatus.DETECTING_MANIPULATION)
            await self._emit(verification_id, "manipulation_detection_start", {})

            manipulation_task = asyncio.create_task(
                self._ai.detect_manipulation(normalized, language)
            )

            # ── 3. Extraer claims ──
            await self._set_status(verification_id, VerificationStatus.EXTRACTING_CLAIMS)
            await self._emit(verification_id, "claims_extraction_start", {})
            extracted_claims, _ = await self._ai.extract_claims(normalized, language)

            # Persistir claims + manipulation signals
            manipulation_findings, _ = await manipulation_task

            uow = self._uow_factory()
            claim_ids: list[tuple[UUID, str, ClaimType, str | None, list[str]]] = []
            async with uow:
                for f in manipulation_findings:
                    uow.session.add(ManipulationSignalModel(
                        verification_id=verification_id,
                        signal_type=f.signal_type,
                        severity=f.severity,
                        explanation=f.explanation,
                        evidence_passage=f.evidence_passage,
                    ))

                for i, c in enumerate(extracted_claims):
                    claim_type = ClaimType(c.claim_type)
                    cm = ClaimModel(
                        verification_id=verification_id,
                        position=i,
                        text=c.text,
                        claim_type=claim_type,
                        context=c.context,
                        keywords=c.keywords,
                    )
                    uow.session.add(cm)
                    await uow.session.flush()
                    claim_ids.append((cm.id, c.text, claim_type, c.context, c.keywords))

            await self._emit(verification_id, "claims_extracted", {
                "count": len(extracted_claims),
                "claims": [
                    {"id": str(cid), "text": txt, "type": ct.value}
                    for cid, txt, ct, _, _ in claim_ids
                ],
            })
            await self._emit(verification_id, "manipulation_detected", {
                "count": len(manipulation_findings),
                "signals": [
                    {
                        "type": f.signal_type,
                        "severity": f.severity,
                        "explanation": f.explanation,
                    }
                    for f in manipulation_findings
                ],
            })

            # ── 4. Por cada claim factual: search + fetch + reason ──
            await self._set_status(verification_id, VerificationStatus.SEARCHING_EVIDENCE)

            confidence_per_claim: dict[UUID, Any] = {}

            for cid, ctext, ctype, ccontext, ckeywords in claim_ids:
                if ctype != ClaimType.FACTUAL:
                    continue  # solo claims factuales se verifican
                await self._process_claim(
                    verification_id, cid, ctext, ccontext, ckeywords, language,
                    confidence_per_claim,
                )

            # ── 5. Componer reporte ──
            await self._set_status(verification_id, VerificationStatus.COMPOSING_REPORT)
            await self._emit(verification_id, "composing_report", {})

            # Score global = promedio ponderado por número de evidencias
            if confidence_per_claim:
                total_value = sum(c.value for c in confidence_per_claim.values())
                global_score = total_value // len(confidence_per_claim)
                # Veredicto global = predominante (simplificación)
                verdicts = [c.verdict for c in confidence_per_claim.values()]
                global_verdict = max(set(verdicts), key=verdicts.count)
            else:
                global_score = 0
                global_verdict = Verdict.INSUFFICIENT_EVIDENCE

            # Headline + summary + conclusion (generados a partir del normalized)
            headline = (
                normalized[:120].rstrip() + ("..." if len(normalized) > 120 else "")
            ).split("\n")[0]
            n_claims = len(claim_ids)
            n_factual = sum(1 for _, _, t, _, _ in claim_ids if t == ClaimType.FACTUAL)

            summary = (
                f"Se identificaron {n_claims} afirmaciones ({n_factual} factuales) "
                f"y se buscó evidencia en múltiples fuentes independientes. "
                f"Score global de confianza: {global_score}/100."
            )
            conclusion = (
                f"{global_verdict.label_es}. "
                "Revisa el desglose por afirmación y las fuentes citadas para evaluar críticamente."
            )

            uow = self._uow_factory()
            async with uow:
                report = ReportModel(
                    verification_id=verification_id,
                    headline=headline,
                    summary=summary,
                    executive_conclusion=conclusion,
                    confidence_value=global_score,
                    verdict=global_verdict,
                    confidence_breakdown={
                        "per_claim": {
                            str(cid): {
                                "value": c.value,
                                "verdict": c.verdict.value,
                                "factors": [
                                    {
                                        "name": f.name,
                                        "value": round(f.value, 3),
                                        "weight": f.weight,
                                        "explanation": f.explanation,
                                    }
                                    for f in c.factors
                                ],
                            }
                            for cid, c in confidence_per_claim.items()
                        }
                    },
                    language=language,
                )
                uow.session.add(report)

                v = (await uow.session.execute(
                    select(VerificationModel).where(VerificationModel.id == verification_id)
                )).scalar_one()
                v.status = VerificationStatus.COMPLETED
                v.completed_at = datetime.now(UTC)

            await self._emit(verification_id, "completed", {
                "confidence_value": global_score,
                "verdict": global_verdict.value,
            })
            logger.info("verify_pipeline_done", verification_id=str(verification_id),
                        score=global_score)

        except Exception as e:
            logger.exception("verify_pipeline_failed", verification_id=str(verification_id))
            await self._set_status(
                verification_id, VerificationStatus.FAILED, error_message=str(e)[:500]
            )
            await self._emit(verification_id, "failed", {"error": str(e)[:500]})

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    async def _ingest(self, input_type: InputType, input_raw: str) -> tuple[str, str | None, str | None]:
        """Devuelve (texto_normalizado, source_url, idioma)."""
        if input_type == InputType.TEXT or input_type == InputType.SOCIAL_POST:
            from langdetect import detect, LangDetectException
            try:
                lang = detect(input_raw[:2000])
            except LangDetectException:
                lang = None
            return input_raw, None, lang

        if input_type in (InputType.URL, InputType.YOUTUBE):
            for fetcher in self._fetchers:
                if await fetcher.can_handle(input_raw):
                    content: FetchedContent = await fetcher.fetch(input_raw)
                    return content.text, content.canonical_url, content.language
            raise ValueError(f"Ningún fetcher pudo manejar la URL: {input_raw}")

        raise NotImplementedError(f"Input type aún no soportado: {input_type}")

    async def _process_claim(
        self,
        verification_id: UUID,
        claim_id: UUID,
        claim_text: str,
        claim_context: str | None,
        keywords: list[str],
        language: str,
        confidence_per_claim: dict,
    ) -> None:
        await self._emit(verification_id, "claim_processing_start", {
            "claim_id": str(claim_id), "text": claim_text[:200],
        })

        # 4a. Generar queries
        queries, _ = await self._ai.generate_queries(claim_text, claim_context, keywords, language)
        await self._emit(verification_id, "queries_generated", {
            "claim_id": str(claim_id), "queries": queries,
        })

        # 4b. Buscar (fan-out a todos los proveedores disponibles)
        all_results = []
        for q in queries[:3]:  # max 3 queries por claim para controlar costo
            for provider in self._search_providers:
                if not await provider.is_available():
                    continue
                try:
                    results = await provider.search(SearchQuery(text=q, max_results=5))
                    all_results.extend(results)
                except Exception as e:
                    logger.warning("search_provider_failed",
                                   provider=provider.name, query=q, error=str(e))

        # Dedup por URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r.url in seen_urls:
                continue
            seen_urls.add(r.url)
            unique_results.append(r)
            if len(unique_results) >= self._max_sources:
                break

        await self._emit(verification_id, "sources_found", {
            "claim_id": str(claim_id),
            "count": len(unique_results),
            "domains": list({extract_domain(r.url) for r in unique_results}),
        })

        # 4c. Fetch contenido en paralelo (con cap)
        fetched: list[tuple[Any, str, str]] = []  # (result, passage, domain)
        async def _fetch_one(r):
            try:
                for fetcher in self._fetchers:
                    if await fetcher.can_handle(r.url):
                        c = await fetcher.fetch(r.url)
                        passage = (c.text or r.snippet)[:1500]
                        return r, passage, c, extract_domain(r.url)
            except Exception as e:
                logger.debug("fetch_failed", url=r.url, error=str(e))
            # Fallback al snippet del motor de búsqueda
            return r, r.snippet, None, extract_domain(r.url)

        fetch_results = await asyncio.gather(
            *[_fetch_one(r) for r in unique_results], return_exceptions=True
        )

        passages_payload: list[dict] = []
        for fr in fetch_results:
            if isinstance(fr, Exception):
                continue
            r, passage, content, domain = fr
            if not passage or len(passage) < 50:
                continue
            passages_payload.append({
                "source_url": r.url,
                "passage": passage,
                "title": r.title,
                "domain": domain,
                "content": content,
                "search_result": r,
            })

        if not passages_payload:
            await self._emit(verification_id, "claim_no_evidence", {"claim_id": str(claim_id)})
            confidence_per_claim[claim_id] = self._calc.calculate([])
            return

        # 4d. Razonar
        await self._set_status(verification_id, VerificationStatus.REASONING)
        ai_passages = [{"source_url": p["source_url"], "passage": p["passage"]} for p in passages_payload]
        reasoning, _ = await self._ai.reason_over_evidence(
            claim_text, claim_context, ai_passages, language
        )

        # Persistir sources + evidence
        evidence_pieces: list[EvidencePiece] = []
        uow = self._uow_factory()
        async with uow:
            for p in passages_payload:
                tier, source_type, notes = lookup(p["source_url"])

                # Encontrar el juicio de la IA sobre este pasaje
                judgment = next(
                    (j for j in (reasoning.supporting_evidence
                                 + reasoning.contradicting_evidence
                                 + reasoning.context_evidence)
                     if j.source_url == p["source_url"]),
                    None,
                )
                if judgment is None:
                    stance = Stance.UNRELATED
                    relevance = 0.0
                else:
                    stance = Stance(judgment.stance)
                    relevance = judgment.relevance_score

                # Upsert source
                content_hash = hashlib.sha256(p["passage"].encode()).hexdigest()
                source = (await uow.session.execute(
                    select(SourceModel).where(SourceModel.canonical_url == p["source_url"])
                )).scalar_one_or_none()

                if source is None:
                    source = SourceModel(
                        canonical_url=p["source_url"],
                        domain=p["domain"],
                        title=p["title"],
                        tier=tier,
                        source_type=source_type,
                        published_at=p["content"].published_at if p["content"] else None,
                        language=p["content"].language if p["content"] else None,
                        methodology_notes=notes,
                        content_hash=content_hash,
                    )
                    uow.session.add(source)
                    await uow.session.flush()

                ev = EvidenceModel(
                    claim_id=claim_id,
                    source_id=source.id,
                    passage=p["passage"][:5000],
                    passage_hash=content_hash,
                    stance=stance,
                    relevance_score=relevance,
                )
                uow.session.add(ev)

                if stance != Stance.UNRELATED:
                    evidence_pieces.append(EvidencePiece(
                        source_domain=p["domain"],
                        tier=tier,
                        stance=stance,
                        relevance_score=relevance,
                        published_at=p["content"].published_at if p["content"] else None,
                    ))

        confidence = self._calc.calculate(evidence_pieces)
        confidence_per_claim[claim_id] = confidence

        await self._emit(verification_id, "claim_completed", {
            "claim_id": str(claim_id),
            "score": confidence.value,
            "verdict": confidence.verdict.value,
            "verdict_label": confidence.verdict.label_es,
            "n_supports": len(reasoning.supporting_evidence),
            "n_contradicts": len(reasoning.contradicting_evidence),
            "n_context": len(reasoning.context_evidence),
            "summary": reasoning.summary,
            "notes_on_contradictions": reasoning.notes_on_contradictions,
        })

    async def _set_status(
        self, verification_id: UUID, status: VerificationStatus, error_message: str | None = None
    ) -> None:
        uow = self._uow_factory()
        async with uow:
            v = (await uow.session.execute(
                select(VerificationModel).where(VerificationModel.id == verification_id)
            )).scalar_one()
            v.status = status
            if error_message:
                v.error_message = error_message

    async def _emit(self, verification_id: UUID, event_type: str, payload: dict) -> None:
        await self._events.publish(verification_id, event_type, payload)
