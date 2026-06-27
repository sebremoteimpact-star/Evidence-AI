"""Adaptador Claude — implementa AIReasoner usando la API de Anthropic.

Estrategia anti-alucinación + anti-injection:
1. Cada prompt define un rol estricto.
2. El contenido del usuario va envuelto en tags `<untrusted_content>`.
3. La salida se fuerza vía tool_use con schema estricto.
4. Validación Pydantic posterior — si Claude se desvía, fallamos en lugar de aceptar basura.
"""

from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field, ValidationError

from evidence_ai.application.ports.ai_reasoner import (
    AIUsage,
    ClaimReasoning,
    EvidenceJudgment,
    ExtractedClaim,
    ManipulationFinding,
)
from evidence_ai.config.settings import Settings
from evidence_ai.infrastructure.ai.prompt_loader import load_prompt, render


# ─── Schemas Pydantic para validar tool_use de Claude ───


class _ClaimItem(BaseModel):
    text: str = Field(min_length=5, max_length=1000)
    claim_type: str = Field(pattern="^(factual|opinion|prediction|normative|unverifiable)$")
    context: str | None = Field(default=None, max_length=2000)
    keywords: list[str] = Field(default_factory=list, max_length=10)


class _ClaimsPayload(BaseModel):
    claims: list[_ClaimItem]


class _FindingItem(BaseModel):
    signal_type: str = Field(
        pattern="^(emotional_language|clickbait|propaganda|misleading_headline|"
        "manipulated_stats|context_manipulation|ai_generated|deepfake_indicator)$"
    )
    severity: str = Field(pattern="^(low|medium|high)$")
    explanation: str = Field(min_length=10, max_length=1000)
    evidence_passage: str | None = Field(default=None, max_length=500)


class _FindingsPayload(BaseModel):
    findings: list[_FindingItem]


class _QueriesPayload(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=8)


class _JudgmentItem(BaseModel):
    passage_index: int = Field(ge=0)
    stance: str = Field(pattern="^(supports|contradicts|context|unrelated)$")
    relevance_score: float = Field(ge=0.0, le=1.0)


class _ReasoningPayload(BaseModel):
    summary: str = Field(min_length=20, max_length=2000)
    judgments: list[_JudgmentItem]
    notes_on_contradictions: str | None = Field(default=None, max_length=2000)


# ─── Definiciones de tools (Claude obliga a salida estructurada) ───

_TOOLS = {
    "submit_claims": {
        "name": "submit_claims",
        "description": "Envía la lista final de claims extraídos del contenido.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "claim_type": {
                                "type": "string",
                                "enum": ["factual", "opinion", "prediction", "normative", "unverifiable"],
                            },
                            "context": {"type": ["string", "null"]},
                            "keywords": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["text", "claim_type", "keywords"],
                    },
                }
            },
            "required": ["claims"],
        },
    },
    "submit_findings": {
        "name": "submit_findings",
        "description": "Envía las señales de manipulación detectadas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "signal_type": {"type": "string"},
                            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                            "explanation": {"type": "string"},
                            "evidence_passage": {"type": ["string", "null"]},
                        },
                        "required": ["signal_type", "severity", "explanation"],
                    },
                }
            },
            "required": ["findings"],
        },
    },
    "submit_queries": {
        "name": "submit_queries",
        "description": "Envía las queries de búsqueda generadas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "queries": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["queries"],
        },
    },
    "submit_reasoning": {
        "name": "submit_reasoning",
        "description": "Envía el razonamiento sobre los pasajes recuperados.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "judgments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "passage_index": {"type": "integer"},
                            "stance": {
                                "type": "string",
                                "enum": ["supports", "contradicts", "context", "unrelated"],
                            },
                            "relevance_score": {"type": "number"},
                        },
                        "required": ["passage_index", "stance", "relevance_score"],
                    },
                },
                "notes_on_contradictions": {"type": ["string", "null"]},
            },
            "required": ["summary", "judgments"],
        },
    },
}


def _wrap_untrusted(content: str, origin: str = "user_input") -> str:
    """Envuelve contenido del usuario en tags. Sanitiza tags de cierre internos."""
    safe = content.replace("</untrusted_content>", "<!--escaped-->")
    return f'<untrusted_content origin="{origin}">\n{safe}\n</untrusted_content>'


class ClaudeAIReasoner:
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())
        self._reasoning_model = settings.claude_reasoning_model
        self._fast_model = settings.claude_fast_model
        self._max_tokens = settings.claude_max_tokens

    async def _call(
        self,
        *,
        model: str,
        system: str,
        user_content: str,
        tool_name: str,
    ) -> tuple[dict[str, Any], AIUsage]:
        """Llamada con tool_use forzado. Devuelve (tool_input, usage)."""
        response = await self._client.messages.create(
            model=model,
            max_tokens=self._max_tokens,
            system=system,
            tools=[_TOOLS[tool_name]],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user_content}],
        )

        usage = AIUsage(
            model=model,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input, usage

        raise RuntimeError(
            f"Claude no usó la tool esperada '{tool_name}'. Respuesta: {response}"
        )

    async def extract_claims(
        self, content: str, language: str
    ) -> tuple[list[ExtractedClaim], AIUsage]:
        system = render(load_prompt("extract_claims"), language=language, max_claims=15)
        wrapped = _wrap_untrusted(content)
        raw, usage = await self._call(
            model=self._reasoning_model,
            system=system,
            user_content=wrapped,
            tool_name="submit_claims",
        )
        try:
            payload = _ClaimsPayload.model_validate(raw)
        except ValidationError as e:
            raise RuntimeError(f"Claude devolvió claims inválidos: {e}") from e
        claims = [
            ExtractedClaim(
                text=c.text,
                claim_type=c.claim_type,
                context=c.context,
                keywords=c.keywords,
            )
            for c in payload.claims
        ]
        return claims, usage

    async def detect_manipulation(
        self, content: str, language: str
    ) -> tuple[list[ManipulationFinding], AIUsage]:
        system = render(load_prompt("detect_manipulation"), language=language)
        wrapped = _wrap_untrusted(content)
        raw, usage = await self._call(
            model=self._reasoning_model,
            system=system,
            user_content=wrapped,
            tool_name="submit_findings",
        )
        try:
            payload = _FindingsPayload.model_validate(raw)
        except ValidationError as e:
            raise RuntimeError(f"Claude devolvió findings inválidos: {e}") from e
        findings = [
            ManipulationFinding(
                signal_type=f.signal_type,
                severity=f.severity,
                explanation=f.explanation,
                evidence_passage=f.evidence_passage,
            )
            for f in payload.findings
        ]
        return findings, usage

    async def generate_queries(
        self,
        claim_text: str,
        context: str | None,
        keywords: list[str],
        language: str,
    ) -> tuple[list[str], AIUsage]:
        system = render(load_prompt("generate_queries"), language=language)
        body = (
            f"<claim>{claim_text}</claim>\n"
            f"<context>{context or ''}</context>\n"
            f"<keywords>{', '.join(keywords)}</keywords>"
        )
        raw, usage = await self._call(
            model=self._fast_model,
            system=system,
            user_content=body,
            tool_name="submit_queries",
        )
        try:
            payload = _QueriesPayload.model_validate(raw)
        except ValidationError as e:
            raise RuntimeError(f"Claude devolvió queries inválidos: {e}") from e
        return payload.queries, usage

    async def reason_over_evidence(
        self,
        claim_text: str,
        claim_context: str | None,
        passages: list[dict[str, Any]],
        language: str,
    ) -> tuple[ClaimReasoning, AIUsage]:
        system = render(load_prompt("reason_evidence"), language=language)

        passages_block = "\n\n".join(
            f"<passage index=\"{i}\" source=\"{p['source_url']}\">\n"
            f"{_wrap_untrusted(p['passage'], origin=p['source_url'])}\n"
            f"</passage>"
            for i, p in enumerate(passages)
        )
        body = (
            f"<claim>{claim_text}</claim>\n"
            f"<claim_context>{claim_context or ''}</claim_context>\n"
            f"<passages>\n{passages_block}\n</passages>"
        )

        raw, usage = await self._call(
            model=self._reasoning_model,
            system=system,
            user_content=body,
            tool_name="submit_reasoning",
        )
        try:
            payload = _ReasoningPayload.model_validate(raw)
        except ValidationError as e:
            raise RuntimeError(f"Claude devolvió reasoning inválido: {e}") from e

        supports, contradicts, context_judgments = [], [], []
        for j in payload.judgments:
            if j.passage_index >= len(passages):
                continue  # Claude alucinó un índice — ignorar
            p = passages[j.passage_index]
            ev = EvidenceJudgment(
                source_url=p["source_url"],
                passage=p["passage"],
                stance=j.stance,
                relevance_score=j.relevance_score,
            )
            if j.stance == "supports":
                supports.append(ev)
            elif j.stance == "contradicts":
                contradicts.append(ev)
            elif j.stance == "context":
                context_judgments.append(ev)

        reasoning = ClaimReasoning(
            summary=payload.summary,
            supporting_evidence=supports,
            contradicting_evidence=contradicts,
            context_evidence=context_judgments,
            notes_on_contradictions=payload.notes_on_contradictions,
        )
        return reasoning, usage
