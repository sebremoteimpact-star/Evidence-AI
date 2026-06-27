"""Cálculo determinista del score de confianza.

CRÍTICO: este cálculo NO lo hace Claude. Se hace en código a partir de la
evidencia recuperada, para que cada reporte sea reproducible y auditable.

Fórmula:
    score = weighted_sum(factors) * 100
    factors:
      - source_count_factor       (¿cuántas fuentes independientes?)
      - tier_quality_factor       (¿qué tier promedio? prioriza primarios)
      - agreement_factor          (¿concuerdan las fuentes?)
      - independence_factor       (¿distintos dominios y publishers?)
      - freshness_factor          (¿qué tan recientes son las fuentes?)
      - coverage_factor           (¿hay evidencia que cubra el claim?)

    veredicto = función del score + balance supports/contradicts
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from evidence_ai.domain.value_objects.confidence_score import (
    ConfidenceFactor,
    ConfidenceScore,
    Verdict,
)
from evidence_ai.domain.value_objects.source_tier import SourceTier
from evidence_ai.domain.value_objects.stance import Stance


@dataclass(frozen=True)
class EvidencePiece:
    """Pieza mínima de evidencia que el calculador necesita."""

    source_domain: str
    tier: SourceTier
    stance: Stance
    relevance_score: float
    published_at: datetime | None


_FACTOR_WEIGHTS = {
    "source_count": 0.20,
    "tier_quality": 0.25,
    "agreement": 0.20,
    "independence": 0.15,
    "freshness": 0.10,
    "coverage": 0.10,
}


class ConfidenceCalculator:
    """Calcula score 0-100 + veredicto a partir de evidencia."""

    def calculate(self, evidence: list[EvidencePiece]) -> ConfidenceScore:
        # Solo evidencia relacionada (excluye UNRELATED)
        relevant = [e for e in evidence if e.stance != Stance.UNRELATED]

        if not relevant:
            return ConfidenceScore(
                value=0,
                verdict=Verdict.INSUFFICIENT_EVIDENCE,
                factors=(
                    ConfidenceFactor(
                        name="source_count",
                        value=0.0,
                        weight=_FACTOR_WEIGHTS["source_count"],
                        explanation="No se encontraron fuentes relevantes para esta afirmación.",
                    ),
                ),
            )

        factors: list[ConfidenceFactor] = []

        # 1. Source count (saturación logarítmica)
        n = len(relevant)
        # 0 fuentes → 0, 3 fuentes → 0.5, 6 fuentes → 0.75, 10+ → ~0.9
        count_value = min(1.0, n / 10.0) if n < 10 else min(1.0, 0.9 + (n - 10) * 0.01)
        factors.append(
            ConfidenceFactor(
                name="source_count",
                value=count_value,
                weight=_FACTOR_WEIGHTS["source_count"],
                explanation=f"{n} fuentes relevantes encontradas.",
            )
        )

        # 2. Tier quality (promedio ponderado por relevancia)
        total_weight = sum(e.relevance_score for e in relevant) or 1.0
        weighted_tier_score = sum(e.tier.weight * e.relevance_score for e in relevant) / total_weight
        factors.append(
            ConfidenceFactor(
                name="tier_quality",
                value=weighted_tier_score,
                weight=_FACTOR_WEIGHTS["tier_quality"],
                explanation=f"Calidad ponderada de las fuentes: {weighted_tier_score:.2f}.",
            )
        )

        # 3. Agreement (qué tan claro es el balance)
        supports = [e for e in relevant if e.stance == Stance.SUPPORTS]
        contradicts = [e for e in relevant if e.stance == Stance.CONTRADICTS]
        s_weight = sum(e.relevance_score * e.tier.weight for e in supports)
        c_weight = sum(e.relevance_score * e.tier.weight for e in contradicts)
        total = s_weight + c_weight
        if total > 0:
            # |s - c| / total → 1.0 si todo apunta a un lado, 0.0 si está 50/50
            agreement = abs(s_weight - c_weight) / total
        else:
            agreement = 0.5  # solo contexto, sin postura
        factors.append(
            ConfidenceFactor(
                name="agreement",
                value=agreement,
                weight=_FACTOR_WEIGHTS["agreement"],
                explanation=(
                    f"Acuerdo entre fuentes: {agreement:.2f} "
                    f"({len(supports)} apoyan, {len(contradicts)} contradicen)."
                ),
            )
        )

        # 4. Independence (proporción de dominios únicos)
        unique_domains = len({e.source_domain for e in relevant})
        independence = unique_domains / n
        factors.append(
            ConfidenceFactor(
                name="independence",
                value=independence,
                weight=_FACTOR_WEIGHTS["independence"],
                explanation=f"{unique_domains} dominios únicos sobre {n} fuentes.",
            )
        )

        # 5. Freshness (proporción de fuentes recientes)
        now = datetime.now(UTC)
        recent_count = 0
        dated_count = 0
        for e in relevant:
            if e.published_at is None:
                continue
            dated_count += 1
            age_days = (now - e.published_at).days
            if age_days < 365 * 2:  # menos de 2 años
                recent_count += 1
        freshness = (recent_count / dated_count) if dated_count > 0 else 0.5
        factors.append(
            ConfidenceFactor(
                name="freshness",
                value=freshness,
                weight=_FACTOR_WEIGHTS["freshness"],
                explanation=(
                    f"{recent_count}/{dated_count} fuentes con fecha publicadas en últimos 2 años."
                    if dated_count > 0
                    else "Pocas fuentes con fecha conocida — no se puede evaluar frescura."
                ),
            )
        )

        # 6. Coverage (proporción de evidencia con relevance alta)
        high_rel = sum(1 for e in relevant if e.relevance_score >= 0.7)
        coverage = high_rel / n
        factors.append(
            ConfidenceFactor(
                name="coverage",
                value=coverage,
                weight=_FACTOR_WEIGHTS["coverage"],
                explanation=f"{high_rel}/{n} fuentes con alta relevancia al claim.",
            )
        )

        # Score compuesto (0-100)
        composite = sum(f.value * f.weight for f in factors)
        score_value = int(round(composite * 100))

        # Veredicto
        verdict = self._derive_verdict(score_value, s_weight, c_weight, n)

        return ConfidenceScore(value=score_value, verdict=verdict, factors=tuple(factors))

    @staticmethod
    def _derive_verdict(score: int, s_weight: float, c_weight: float, n_sources: int) -> Verdict:
        if n_sources < 2 or score < 25:
            return Verdict.INSUFFICIENT_EVIDENCE

        total = s_weight + c_weight
        if total == 0:
            return Verdict.INSUFFICIENT_EVIDENCE

        balance = (s_weight - c_weight) / total  # rango [-1, 1]

        # Mixed si hay contradicción significativa
        if abs(balance) < 0.30:
            return Verdict.MIXED

        if balance > 0.7 and score >= 70:
            return Verdict.STRONGLY_SUPPORTED
        if balance > 0:
            return Verdict.SUPPORTED
        if balance < -0.7 and score >= 70:
            return Verdict.STRONGLY_CONTRADICTED
        return Verdict.CONTRADICTED
