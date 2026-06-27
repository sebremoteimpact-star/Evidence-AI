# ADR 0006 — SSE en lugar de WebSockets para progreso en vivo

**Estado:** Aceptado · **Fecha:** 2026-06-26 · **Fase:** 2

## Contexto

Una verificación tarda 60-180s. El usuario necesita ver progreso en vivo (claim extraído, fuente encontrada, evidencia rankeada, ...) en lugar de un spinner ciego.

## Decisión

Usamos **Server-Sent Events (SSE)** para enviar eventos del backend al frontend.

## Alternativas consideradas

- **WebSockets:** rechazado. Bidireccional, pero solo necesitamos servidor→cliente. Más complejo: protocolo binario, gestión de conexión, frame fragmentación. Vercel free no soporta WS persistentes; Render sí, pero complica.
- **Long polling:** rechazado. Latencia alta, requests repetidas, peor UX.
- **GraphQL Subscriptions:** rechazado por overkill — no usamos GraphQL.

## Consecuencias

**Positivas:**
- HTTP estándar, atraviesa proxies/CDN sin config especial.
- API nativa `EventSource` en el navegador, sin librerías.
- Reconexión automática del cliente.
- Vercel + Render lo soportan sin problemas.

**Negativas:**
- Solo unidireccional (servidor → cliente). Si necesitamos chat o colaboración en tiempo real, agregamos WS para ese caso específico.
- Límite de conexiones por dominio en HTTP/1.1 (mitigado por HTTP/2, que ambas plataformas soportan).

## Implementación

- Backend: `sse-starlette` en endpoint `GET /stream/{verification_id}`.
- Bus: Redis pubsub. El worker publica eventos; el endpoint SSE los suscribe y reenvía.
- Frontend: `EventSource` envuelto en un hook React tipado (`useVerification`).
