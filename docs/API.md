# API REST — Evidence AI

> Documento se completará en Fase 5.
> En runtime, los docs interactivos están en `http://localhost:8000/docs` (Swagger UI) y `/redoc`.

## Convenciones

- Versionado en path: `/api/v1/...`
- Auth: `Authorization: Bearer <jwt>`
- Errores en formato [RFC 7807 Problem Details](https://datatracker.ietf.org/doc/html/rfc7807).
- IDs: ULIDs (sortable, URL-safe).
- Timestamps: ISO 8601 con timezone UTC.
- Paginación: cursor-based (`?cursor=...&limit=20`).

## Endpoints principales (preview)

- `POST /api/v1/verifications` — crear verificación
- `GET /api/v1/verifications/{id}` — obtener estado/reporte
- `GET /api/v1/stream/{id}` — SSE: progreso en vivo
- `GET /api/v1/verifications` — historial del usuario
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`
- `GET /api/v1/health`
