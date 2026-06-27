# @evidence-ai/shared-types

Tipos TypeScript auto-generados desde el esquema OpenAPI del backend.

**No editar a mano.** El archivo `src/api.generated.ts` se regenera con:

```bash
# Desde el raíz del repo, con el API corriendo en localhost:8000
make types

# O directamente
pnpm --filter @evidence-ai/shared-types generate
```

El frontend (`apps/web`) lo importa así:

```ts
import type { paths, components } from "@evidence-ai/shared-types";

type Verification = components["schemas"]["VerificationResponse"];
```

Esto garantiza que cualquier cambio en los schemas Pydantic del backend rompa el typecheck del frontend en CI, antes de llegar a producción.
