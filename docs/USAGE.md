# Guía de uso — Evidence AI

Esta guía cubre cómo arrancar el sistema, cómo usarlo, y cómo interpretar los reportes.

---

## 1. Requisitos

- **Docker Desktop** corriendo
- **Node 20+** y **pnpm** (`npm install -g pnpm`)
- **Python 3.12+** y **uv** (`pip install uv` o instalador de Astral)
- Una **API key de Anthropic** ([console.anthropic.com](https://console.anthropic.com/))

DuckDuckGo es gratis sin API key — no necesitas más para el modo básico.

---

## 2. Primera puesta en marcha

```powershell
# 1. Clonar e ir al directorio
cd C:\Users\DELL\Projects\evidence-ai

# 2. Bootstrap (copia .env.example → .env, levanta postgres + redis)
.\scripts\dev-up.ps1

# 3. Editar apps\api\.env y agregar:
#    ANTHROPIC_API_KEY=sk-ant-...
#    JWT_SECRET=<32+ caracteres aleatorios>   (genera con: openssl rand -base64 32)

# 4. Instalar dependencias
cd apps\api
uv sync
cd ..\web
pnpm install
cd ..\..

# 5. Aplicar migraciones a la DB
make migrate
#   o manualmente: cd apps\api && uv run alembic upgrade head

# 6. Arrancar todo
make dev
#   o en terminales separadas:
#     cd apps\api && uv run uvicorn evidence_ai.interfaces.http.app:create_app --factory --reload
#     cd apps\api && uv run arq evidence_ai.interfaces.worker.arq_worker.WorkerSettings
#     cd apps\web && pnpm dev
```

Abre:
- **Aplicación:** http://localhost:3000
- **Docs API (Swagger):** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

---

## 3. Cómo usar la aplicación

### Crear cuenta

Visita http://localhost:3000 → "Crear cuenta gratis". Email + contraseña (mínimo 10 caracteres). Te logueamos automáticamente.

### Verificar contenido

Tres modos:

1. **Texto:** pega una noticia, post, transcript o cualquier texto (hasta 50.000 caracteres).
2. **URL:** un enlace a un artículo. Extraemos el texto canónico (sin nav/sidebar/ads).
3. **YouTube:** un enlace a video con subtítulos disponibles. Usamos el transcript.

Pulsa "Verificar evidencia". Verás el progreso **en vivo, paso a paso:**

```
✓ Contenido extraído         (50.000 caracteres · idioma: es)
✓ Análisis de manipulación   (2 señales detectadas)
✓ Afirmaciones identificadas (8 afirmaciones, 5 factuales)
↻ Verificando afirmación 1   (3 queries generadas · 7 fuentes en 5 dominios)
  ✓ Score 78/100 · 4 apoyan · 1 contradice · 2 contexto
↻ Verificando afirmación 2   ...
✓ Componiendo reporte
✓ Verificación completa
```

### El reporte

Tras completarse, te llevamos al reporte. Tiene:

- **Veredicto calibrado** (banner principal):
  - "La evidencia apoya fuertemente"
  - "La evidencia apoya"
  - "La evidencia es mixta"
  - "La evidencia contradice"
  - "La evidencia contradice fuertemente"
  - "Evidencia insuficiente"
  - **Jamás "verdadero" o "falso".**

- **Score 0-100** animado, con desglose por 6 factores:
  - `source_count`: cuántas fuentes independientes.
  - `tier_quality`: calidad media (peer-reviewed pesa más que blog).
  - `agreement`: qué tan claro es el balance supports/contradicts.
  - `independence`: proporción de dominios únicos.
  - `freshness`: proporción de fuentes recientes.
  - `coverage`: proporción de evidencia con alta relevancia.

- **Por cada afirmación:** evidencia que apoya, contradice y aporta contexto, con citas exactas y enlaces a la fuente.

- **Señales de manipulación** detectadas en el input original (con explicación didáctica).

---

## 4. Cómo interpretar el reporte

Reglas para usar Evidence AI con criterio:

1. **El score no es una nota.** Es el peso de la evidencia disponible *en este momento*. Una verificación con score 30 puede subir a 80 si aparecen nuevas fuentes.

2. **Lee siempre las fuentes citadas.** El sistema te da los enlaces — no te quedes con la conclusión, comprueba los originales.

3. **Si el veredicto es "mixto" o "evidencia insuficiente", no concluyas.** Significa que la realidad no permite una respuesta clara aún.

4. **Mira los tiers.** 10 fuentes tier 6 (periodismo) pesan menos que 2 tier 1 (peer-reviewed).

5. **Las señales de manipulación NO invalidan el contenido.** Un titular clickbait puede señalar un hecho verdadero. Las señales solo te dicen "ten cuidado al leer", no "esto es falso".

6. **Para temas políticos**, busca diversidad de perspectivas. Si todas las fuentes son del mismo lado, el reporte mismo lo señalará.

---

## 5. Limitaciones conocidas (v0.1)

- **DuckDuckGo limita el rate.** Si haces muchas verificaciones rápidas, algunas búsquedas devolverán pocos resultados. Solución: agrega una API key de Brave o Google CSE en `.env`.

- **Solo verifica afirmaciones factuales.** Opiniones, predicciones y juicios normativos se identifican y reportan, pero no se buscan en fuentes (no tendría sentido).

- **YouTube requiere subtítulos.** Videos sin captions no se pueden procesar todavía. Sube el transcript manualmente como texto.

- **Análisis de video = solo transcript.** No analizamos frames para detectar deepfakes en v1. Lo que detectamos son inconsistencias entre metadata y transcript.

- **El reporte se genera en el idioma del input.** Si pegas algo en inglés, el reporte saldrá en inglés. Para forzar idioma, configura tu locale de usuario.

---

## 6. Para desarrolladores

- Arquitectura: ver [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Decisiones: ver [`DECISIONS/`](DECISIONS/)
- API: http://localhost:8000/docs (Swagger UI con todos los endpoints)
- Prompts: `apps/api/src/evidence_ai/infrastructure/ai/prompts/*.md` (versionados)
- Source registry: `packages/source-registry/registry.json` (agrega dominios aquí)

### Comandos útiles

```powershell
make dev            # levanta todo
make dev-db         # solo postgres + redis
make migrate        # aplica migraciones
make migration MSG="agregar tabla X"   # nueva migración autogenerada
make test           # test suite completa
make lint           # ruff + eslint + import-linter
make format         # auto-format
make types          # regenera tipos TS desde OpenAPI
```

---

## 7. Reportar problemas

Issues en GitHub. Para vulnerabilidades de seguridad ver [`SECURITY.md`](SECURITY.md).
