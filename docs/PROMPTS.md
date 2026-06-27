# Diseño de prompts — Evidence AI

> Documento se completará en Fase 9 (motor de razonamiento).

## Principios

1. **Contenido del usuario es DATOS, no instrucciones.** Va envuelto en `<untrusted_content>` con instrucción al modelo de tratarlo como tal.
2. **Salida estructurada vía tool use.** Nada de "responde en formato JSON" — usamos la API de tools de Claude para forzar el schema.
3. **Plantillas versionadas** en `apps/api/src/evidence_ai/infrastructure/ai/prompts/`.
4. **Sin URLs en la salida.** Las URLs vienen de los retrievals, no del modelo. Esto previene alucinación de citas.
5. **Calibración explícita.** Cuando hay evidencia insuficiente, el prompt fuerza al modelo a decirlo en lugar de inventar.

## Estructura de prompts

```
prompts/
├── _shared/
│   └── safety_preamble.md       # incluido en todos los prompts
├── extract_claims.md
├── detect_manipulation.md
├── generate_queries.md
├── reason_evidence.md
└── compose_report.md
```

Detalle pendiente.
