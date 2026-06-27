# Seguridad — Evidence AI

> Documento se completará en Fase 14 (hardening de producción).

## Reportar una vulnerabilidad

Por favor reporta vulnerabilidades de forma privada — **no abras issues públicos** para problemas de seguridad.

Email: (pendiente de definir)

## Modelo de amenazas

Ver [`ARCHITECTURE.md`](ARCHITECTURE.md) sección 9.

## Checklist OWASP ASVS L2

(Pendiente — Fase 14.)

## Política de claves y secretos

- Todas las claves se inyectan vía variables de entorno.
- Rotación documentada en `DEPLOYMENT.md`.
- Pre-commit hook `gitleaks` previene commits accidentales.
