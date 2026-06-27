# Guía de Despliegue — Evidence AI (cero local)

Esta guía despliega **Evidence AI completo en la nube**, totalmente gratis, sin que tengas que instalar Docker/Python/Node localmente. Solo necesitas Git y un navegador.

> ⏱️ **Tiempo total estimado:** 45-75 minutos (incluyendo crear cuentas)
> 💰 **Costo:** $0/mes en todos los servicios (free tier)
> ⚠️ **Único gasto posible:** Claude API si superas los $5 de crédito de prueba (~500 verificaciones)

---

## Topología final

```
Usuario ──HTTPS──> Vercel (Next.js)
                      │
                      └─REST/SSE─> Render Web (FastAPI)
                                       │
                                       ├──> Supabase (Postgres + pgvector)
                                       ├──> Upstash (Redis)
                                       └──> Claude API
                                       │
                                  encola trabajos
                                       ▼
                                  Render Worker (arq)
```

| Servicio | Plataforma | Free tier |
|---|---|---|
| Frontend (Next.js) | **Vercel** | Hobby — 100 GB bandwidth/mes |
| API (FastAPI) | **Render** Web Service | 750h/mes (sleeps tras inactividad) |
| Worker (arq) | **Render** Background Worker | 750h/mes |
| Postgres + pgvector | **Supabase** | 500 MB, 50k MAU |
| Redis | **Upstash** | 10k requests/día, 256 MB |
| Claude API | **Anthropic** | $5 crédito de prueba |

---

## Paso 0 — Instalar Git

Único software local requerido. Git es ~50 MB, no requiere admin para la versión "portable".

**Windows (lo más rápido):**
1. Descarga el instalador: https://git-scm.com/download/win
2. Ejecuta el `.exe`. Acepta todos los defaults. Marca "Git from the command line and also from 3rd-party software".
3. Verifica abriendo PowerShell:
   ```powershell
   git --version
   # Debe mostrar: git version 2.x.x
   ```

---

## Paso 1 — Crear cuenta GitHub y subir el repo (10 min)

### 1.1 Cuenta GitHub
Si no tienes: https://github.com/signup — gratis, solo necesitas email.

### 1.2 Crear repositorio vacío
1. Login → click el **+** arriba a la derecha → **New repository**
2. **Repository name:** `evidence-ai`
3. **Visibility:** Public (los free tiers de Render/Vercel funcionan mejor con repos públicos)
4. **NO** marques "Add a README" — el repo ya lo tiene
5. Click **Create repository**

GitHub te muestra una URL como `https://github.com/TU_USUARIO/evidence-ai.git`. Cópiala.

### 1.3 Configurar Git localmente (primera vez)

En PowerShell:
```powershell
cd C:\Users\DELL\Projects\evidence-ai

# Configurar tu identidad (una sola vez)
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

# Conectar al repo remoto y subir
git remote add origin https://github.com/TU_USUARIO/evidence-ai.git
git branch -M main
git push -u origin main
```

GitHub te pedirá autenticación. La forma moderna es:
- **Opción A (recomendada):** Instalar [GitHub CLI](https://cli.github.com/) y correr `gh auth login`. Te logueas con el navegador.
- **Opción B:** Crear un Personal Access Token: https://github.com/settings/tokens (scope `repo`). Cuando Git pida password, pega el token.

Si el push fue exitoso, ve a la URL de tu repo y verifica que veas los archivos.

---

## Paso 2 — Crear Postgres en Supabase (5 min)

Postgres con extensión `pgvector` ya habilitada — perfecto para nosotros.

1. Crea cuenta gratis: https://supabase.com → Sign up con GitHub.
2. Click **New project**:
   - **Name:** `evidence-ai`
   - **Database Password:** **Genera uno fuerte y guárdalo** (no se puede recuperar)
   - **Region:** la más cercana a ti
   - **Pricing Plan:** Free
3. Click **Create new project**. Espera ~2 min mientras provisiona.

### 2.1 Habilitar pgvector
1. En el menú izquierdo → **Database** → **Extensions**
2. Busca `vector` → click el toggle para habilitarla
3. (Las otras: `pg_trgm`, `citext`, `pgcrypto` ya vienen habilitadas por defecto en Supabase, no hace falta tocar)

### 2.2 Obtener el connection string
1. **Project Settings** (icono de engranaje, abajo izq) → **Database**
2. Scroll hasta **Connection string** → tab **URI**
3. Verás algo como:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghij.supabase.co:5432/postgres
   ```
4. **Reemplaza `[YOUR-PASSWORD]`** por la password que generaste en el paso 2
5. **IMPORTANTE: cambia `postgresql://` por `postgresql+asyncpg://`** (Evidence AI usa el driver async)

Connection string final, ejemplo:
```
postgresql+asyncpg://postgres:miPasswordSegura123@db.abcdefghij.supabase.co:5432/postgres
```

📋 **Guárdalo** — lo pegarás en Render como `DATABASE_URL`.

---

## Paso 3 — Crear Redis en Upstash (3 min)

1. Crea cuenta gratis: https://upstash.com → Sign up con GitHub
2. Click **Create Database** (tab Redis):
   - **Name:** `evidence-ai-redis`
   - **Type:** Regional
   - **Region:** la más cercana al región de Render (Oregon si dejas el default)
   - **TLS:** Enabled (rediss://)
3. Click **Create**

### 3.1 Obtener el connection string
1. En la página del database → sección **Connect to your database**
2. Cambia el dropdown a **redis-cli** o **Endpoint**
3. Copia la URL con formato `rediss://default:PASSWORD@xxxxx.upstash.io:6379`

📋 **Guárdalo** — lo pegarás en Render como `REDIS_URL`.

---

## Paso 4 — Obtener API key de Anthropic (5 min)

1. Crea cuenta en https://console.anthropic.com
2. Verifica tu email
3. Anthropic te da **$5 de crédito de prueba** sin tarjeta
4. En la consola → **API Keys** → **Create Key** → dale un nombre como `evidence-ai-prod`
5. **Copia la key** (formato `sk-ant-...`) — solo se muestra una vez

📋 **Guárdalo** — lo pegarás en Render como `ANTHROPIC_API_KEY`.

---

## Paso 5 — Desplegar backend en Render (15 min)

1. Crea cuenta gratis: https://render.com → Sign up con GitHub
2. **Dashboard** → click **New** → **Blueprint**
3. Conecta tu repositorio `evidence-ai`
4. Render detecta automáticamente `infra/render/render.yaml` y te muestra los servicios que creará: `evidence-ai-api` y `evidence-ai-worker`
5. Click **Apply**

### 5.1 Configurar las variables de entorno

Render te pedirá los valores de las env vars marcadas `sync: false`. Pega:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | Connection string de Supabase (el del paso 2) — **mismo valor en API y Worker** |
| `REDIS_URL` | Connection string de Upstash (el del paso 3) — **mismo valor en API y Worker** |
| `ANTHROPIC_API_KEY` | Tu key de Anthropic (el del paso 4) — **mismo valor en API y Worker** |
| `CORS_ORIGINS` | **Déjalo vacío por ahora** — lo configuramos después de desplegar el frontend |
| `BRAVE_SEARCH_API_KEY` | Vacío (opcional, mejora cobertura si la tienes) |
| `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ID` | Vacíos |
| `JWT_SECRET` (worker) | **Mismo valor que el API** — copia el que Render generó automáticamente para el API |

Para `JWT_SECRET` en el worker:
1. Primero deja que el API arranque y genere su `JWT_SECRET`
2. Ve a **evidence-ai-api → Environment** → copia el `JWT_SECRET`
3. Ve a **evidence-ai-worker → Environment** → pega el mismo valor

### 5.2 Esperar el primer deploy

- El **API** tarda ~5-8 min (descarga Docker, instala deps, corre migraciones Alembic, arranca)
- El **Worker** tarda lo mismo

Verifica:
- API: en su página verás **Logs** — deberías ver `api_started`
- Click **URL** (ej: `https://evidence-ai-api.onrender.com`) → te lleva a tu API
- Visita `https://TU-API.onrender.com/health` → debe devolver `{"status":"ok"}`
- Visita `https://TU-API.onrender.com/docs` → ves Swagger UI con todos los endpoints

📋 **Guarda la URL del API** — la pegarás en Vercel como `NEXT_PUBLIC_API_URL`.

> ⚠️ **Free tier de Render:** los servicios "duermen" tras 15 min de inactividad. El primer request tras dormir tarda ~30s. Para verificar esto no es problema en producción real, pero para desarrollo está bien.

---

## Paso 6 — Desplegar frontend en Vercel (10 min)

1. Crea cuenta gratis: https://vercel.com → Sign up con GitHub
2. **Dashboard** → **Add New** → **Project**
3. Selecciona tu repo `evidence-ai` → click **Import**
4. **Configure Project:**
   - **Framework Preset:** Next.js (auto-detectado)
   - **Root Directory:** click **Edit** → escribe `apps/web` → **Continue**
   - **Build Command:** déjalo en default (Vercel usará `pnpm build`)
   - **Output Directory:** déjalo en default (`.next`)
   - **Install Command:** déjalo en default (`pnpm install`)

5. **Environment Variables:**
   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | URL del API de Render (ej: `https://evidence-ai-api.onrender.com`) |
   | `AUTH_SECRET` | Genera uno: en una terminal `openssl rand -base64 32` (o usa cualquier random de 32+ chars) |

6. Click **Deploy**

Espera 2-4 min. Vercel te dará una URL como `https://evidence-ai.vercel.app`.

---

## Paso 7 — Cerrar el círculo: configurar CORS (2 min)

Render no sabe el dominio de Vercel hasta que lo desplegamos. Ahora se lo decimos:

1. Vuelve a Render → **evidence-ai-api** → **Environment**
2. Edita `CORS_ORIGINS` y pega la URL completa de Vercel:
   ```
   https://evidence-ai.vercel.app
   ```
   (Si tienes un dominio custom, agrégalo separado por coma)

3. Click **Save Changes** — Render hace redeploy automáticamente (~2 min)

> ✅ El regex `https://.*\.vercel\.app` ya viene configurado en `render.yaml`, así que **todos los preview deployments de Vercel** (cada PR genera uno) funcionan automáticamente.

---

## Paso 8 — Verificar que todo funciona

1. Visita tu URL de Vercel: `https://evidence-ai.vercel.app`
2. Click **Crear cuenta gratis** → registra un usuario
3. Vas al dashboard → click **Verificar**
4. Pega una noticia o URL → **Verificar evidencia**
5. Deberías ver el timeline animado en vivo y luego el reporte completo

---

## Troubleshooting

### "Network error" al registrarse
- ¿`CORS_ORIGINS` en Render incluye tu dominio Vercel?
- ¿`NEXT_PUBLIC_API_URL` en Vercel apunta a tu API Render?
- Abre DevTools → Network → busca el error en el request

### El API no responde / cold start
- Free tier de Render duerme tras 15 min. Primer request tarda 30s.
- Verifica en Render → **Logs** que el API arrancó correctamente.

### "alembic command not found" en preDeploy
- Verifica que el Dockerfile haga `uv sync` correctamente.
- En Render → **Settings** → puedes desactivar `preDeployCommand` temporalmente y correr migraciones manualmente vía **Shell**:
  ```bash
  /app/.venv/bin/alembic upgrade head
  ```

### Verificación se queda en "pending" para siempre
- El worker no procesa. Verifica:
  - **evidence-ai-worker** en Render está corriendo (no en error)
  - Su `REDIS_URL` y `DATABASE_URL` son los **mismos** que el API
  - Logs del worker — busca `worker_started`

### Claude devuelve 401
- API key inválida o sin créditos
- Verifica en https://console.anthropic.com → **Usage**

### Supabase 500 errors / connection refused
- Free tier de Supabase pausa el proyecto tras 7 días de inactividad
- En el dashboard de Supabase puedes "Restore" el proyecto

### CORS sigue fallando
- Verifica que la URL de Vercel **no termine en `/`**
- Si usas custom domain, agrégalo a `CORS_ORIGINS`

---

## Actualizar el código en producción

Cualquier `git push origin main` dispara:
- Vercel rebuilds el frontend automáticamente
- Render rebuilds API + Worker automáticamente
- Migraciones Alembic corren en pre-deploy del API

```powershell
cd C:\Users\DELL\Projects\evidence-ai
# haces cambios...
git add .
git commit -m "fix: lo que sea"
git push
```

---

## Costos reales

Después de 1 mes de uso ligero (10 verificaciones/día):

| Servicio | Costo mensual |
|---|---|
| Vercel | $0 (muy lejos del límite) |
| Render API | $0 (750h cubren un servicio activo siempre) |
| Render Worker | $0 (mismo) |
| Supabase | $0 (muy lejos de 500 MB) |
| Upstash | $0 (10k req/día = 300k/mes, sobra) |
| Anthropic Claude | ~$3-8/mes con ~300 verificaciones |
| **Total** | **$3-8/mes** |

Para uso real público necesitas plan paid de Render ($7/mes) para evitar cold starts.
