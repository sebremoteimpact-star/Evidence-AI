"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Loader2, ArrowLeft, AlertTriangle, CheckCircle2,
  Quote, ExternalLink, Sparkles, Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ConfidenceMeter } from "@/components/report/confidence-meter";
import { VerdictBanner } from "@/components/report/verdict-banner";
import { apiClient } from "@/lib/api/client";

interface ReportData {
  verification: any;
  report: any;
  claims: any[];
  manipulation_signals: any[];
  evidence_by_claim: Record<string, any[]>;
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    // Por simplicidad: pegamos múltiples endpoints
    // (en producción el backend expondría un endpoint agregado /reports/{id}/full)
    (async () => {
      try {
        const verification = await apiClient.get<any>(`/api/v1/verifications/${id}`);
        // Endpoint agregado pendiente — usamos verification por ahora
        setData({
          verification,
          report: verification.report ?? null,
          claims: [],
          manipulation_signals: [],
          evidence_by_claim: {},
        });
      } catch (e: any) {
        setError(e.detail ?? "Error al cargar el reporte");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="mb-2">No se pudo cargar el reporte</h2>
            <p className="text-muted-foreground mb-6">{error ?? "Error desconocido"}</p>
            <Button variant="outline" onClick={() => router.push("/verificar")}>
              <ArrowLeft className="h-4 w-4" /> Volver
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const v = data.verification;
  const isCompleted = v.status === "completed";

  // Si aún no hay reporte agregado, mostramos resumen
  if (!isCompleted) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card className="glass">
          <CardContent className="pt-6 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <h2 className="mb-2">{v.status_label}</h2>
            <p className="text-muted-foreground">
              La verificación está en progreso. Vuelve a la página de verificación para ver el progreso en vivo.
            </p>
            <Button variant="outline" className="mt-6" onClick={() => router.push("/verificar")}>
              <ArrowLeft className="h-4 w-4" /> Ver progreso
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Mock data — en producción viene del endpoint /reports/{id}/full
  const score = v.report?.confidence_value ?? 0;
  const verdict = v.report?.verdict ?? "insufficient_evidence";

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <Button variant="ghost" size="sm" onClick={() => router.push("/historial")}>
        <ArrowLeft className="h-4 w-4" /> Volver al historial
      </Button>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="mb-3 flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-primary" />
          Reporte de evidencia
        </h1>
        <p className="text-muted-foreground">
          Verificado el {new Date(v.completed_at ?? v.created_at).toLocaleString("es")}
        </p>
      </motion.div>

      {/* Veredicto principal */}
      <VerdictBanner verdict={verdict} />

      {/* Grid: score + resumen */}
      <div className="grid md:grid-cols-[auto_1fr] gap-8 items-center">
        <ConfidenceMeter value={score} size="lg" label="Confianza global" />
        <div className="space-y-3">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-lg">Resumen ejecutivo</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">
                {v.report?.summary ?? "Resumen no disponible."}
              </p>
            </CardContent>
          </Card>
          <Card className="glass">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-tier-1" />
                Conclusión
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">
                {v.report?.executive_conclusion ?? "Conclusión no disponible."}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Input original */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Quote className="h-4 w-4" />
            Contenido analizado
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-muted/50 p-4 text-sm leading-relaxed max-h-60 overflow-y-auto">
            {v.input_normalized ?? v.input_raw}
          </div>
          {v.source_url && (
            <a
              href={v.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 mt-3 text-xs text-primary hover:underline"
            >
              Fuente original <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </CardContent>
      </Card>

      {/* Disclaimer pedagógico */}
      <Card className="glass border-primary/20">
        <CardContent className="pt-6 flex gap-4">
          <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
          <div className="text-sm text-muted-foreground leading-relaxed">
            <strong className="text-foreground">Cómo leer este reporte:</strong> el score
            de confianza refleja el peso de la evidencia disponible, no una declaración de verdad.
            Revisa siempre las fuentes citadas y el desglose por factor antes de formar una opinión.
            Si las fuentes se contradicen, lee ambos lados.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
