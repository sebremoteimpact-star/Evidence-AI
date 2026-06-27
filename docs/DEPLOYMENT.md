# Despliegue — Evidence AI

> Documento se completará en Fase 13.

## Topología objetivo (todo free tier)

| Componente | Proveedor | Plan |
|---|---|---|
| Web (Next.js) | Vercel | Hobby (free) |
| API + Worker | Render | Free |
| PostgreSQL | Supabase | Free (500 MB, hasta 50k MAU) |
| Redis | Upstash | Free (10k requests/día) |
| Errores | Sentry | Developer (free) |
| Logs/trazas | Grafana Cloud | Free |

## Variables de entorno

Ver `.env.example` en raíz y en cada `apps/*/`.

## Migraciones en producción

Las migraciones Alembic se ejecutan en un job pre-deploy. (Pendiente: configurar en `render.yaml`.)

## Backups

Supabase free incluye backups diarios automáticos (retención 7 días).
