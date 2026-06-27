"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { InputCard } from "@/components/verification/input-card";
import { ProgressTimeline } from "@/components/verification/progress-timeline";
import { useVerificationStream } from "@/hooks/use-verification-stream";
import { verificationsApi, type InputType } from "@/lib/api/verifications";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export default function VerifyPage() {
  const router = useRouter();
  const [verificationId, setVerificationId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const stream = useVerificationStream(verificationId);

  async function start(type: InputType, raw: string) {
    setError(null);
    setCreating(true);
    try {
      const verification = await verificationsApi.create(type, raw);
      setVerificationId(verification.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Error al crear la verificación");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {!verificationId && (
        <>
          <div className="text-center mb-8">
            <h1 className="mb-3">Verificar evidencia</h1>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Pega contenido y te mostramos qué dice la evidencia disponible —
              en vivo, paso a paso, con citas auditables.
            </p>
          </div>
          <InputCard onSubmit={start} loading={creating} />
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 border border-destructive/30 rounded-lg p-3">
              {error}
            </div>
          )}
        </>
      )}

      {verificationId && (
        <>
          <ProgressTimeline
            events={stream.events}
            isComplete={stream.isComplete}
            isFailed={stream.isFailed}
          />

          {stream.isComplete && (
            <div className="flex justify-center">
              <Button
                variant="gradient"
                size="lg"
                onClick={() => router.push(`/reportes/${verificationId}`)}
              >
                Ver reporte completo <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}

          {stream.isFailed && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                onClick={() => {
                  setVerificationId(null);
                  setError(null);
                }}
              >
                Intentar de nuevo
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
