"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Loader2, ArrowLeft, AlertTriangle, Quote, ExternalLink, Sparkles, Info,
  Database, Globe2, Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfidenceMeter } from "@/components/report/confidence-meter";
import { VerdictBanner } from "@/components/report/verdict-banner";
import { ClaimCard } from "@/components/report/claim-card";
import { ManipulationSignalCard } from "@/components/report/manipulation-signal-card";
import { verificationsApi, type FullVerification } from "@/lib/api/verifications";
import { ApiError } from "@/lib/api/client";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<FullVerification | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    verificationsApi.getFull(id)
      .then(setData)
      .catch((e: unknown) => {
        setError(e instanceof ApiError ? e.detail : "Error al cargar el reporte");
      })
      .finally(() => setLoading(false));
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

  // Si aún no terminó, mostramos placeholder
  if (data.status !== "completed") {
    return (
      <div className="max-w-2xl mx-auto">
        <Card className="glass">
          <CardContent className="pt-6 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <h2 className="mb-2">{data.status_label}</h2>
            <p className="text-muted-foreground">
              La verificación está en progreso.
            </p>
            <Button variant="outline" className="mt-6" onClick={() => router.push("/verificar")}>
              <ArrowLeft className="h-4 w-4" /> Ver progreso en vivo
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const report = data.report;
  const score = report?.confidence_value ?? 0;
  const verdict = report?.verdict ?? "insufficient_evidence";

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <Button variant="ghost" size="sm" onClick={() => router.push("/historial")}>
        <ArrowLeft className="h-4 w-4" /> Volver al historial
      </Button>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="mb-3 flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-primary" />
          Reporte de evidencia
        </h1>
        <p className="text-muted-foreground">
          Verificado el {new Date(data.completed_at ?? data.created_at).toLocaleString("es")}
          {data.language && <span> · idioma detectado: <code className="text-foreground">{data.language}</code></span>}
        </p>
      </motion.div>

      <VerdictBanner verdict={verdict} />

      <div className="grid md:grid-cols-[auto_1fr] gap-8 items-center">
        <ConfidenceMeter value={score} size="lg" label="Confianza global" />
        <div className="space-y-3">
          {report?.headline && (
            <div>
              <h2 className="text-xl font-medium leading-snug">{report.headline}</h2>
            </div>
          )}
          {report?.summary && (
            <Card className="glass">
              <CardHeader><CardTitle className="text-base">Resumen</CardTitle></CardHeader>
              <CardContent><p className="text-sm leading-relaxed">{report.summary}</p></CardContent>
            </Card>
          )}
          {report?.executive_conclusion && (
            <Card className="glass border-primary/20">
              <CardHeader><CardTitle className="text-base">Conclusión</CardTitle></CardHeader>
              <CardContent><p className="text-sm leading-relaxed">{report.executive_conclusion}</p></CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Stats agregados */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={<Layers className="h-4 w-4" />} value={data.stats.total_claims} label="Afirmaciones" />
        <StatCard icon={<Database className="h-4 w-4" />} value={data.stats.total_evidence} label="Piezas de evidencia" />
        <StatCard icon={<Globe2 className="h-4 w-4" />} value={data.stats.unique_domains} label="Dominios únicos" />
        <StatCard icon={<Layers className="h-4 w-4" />} value={data.stats.unique_tiers} label="Tiers cubiertos" />
      </div>

      {/* Afirmaciones */}
      {data.claims.length > 0 && (
        <section>
          <h2 className="mb-4 flex items-center gap-2">
            <Quote className="h-6 w-6 text-muted-foreground" />
            Afirmaciones detectadas
          </h2>
          <div className="space-y-3">
            {data.claims.map((c, i) => <ClaimCard key={c.id} claim={c} index={i} />)}
          </div>
        </section>
      )}

      {/* Señales de manipulación */}
      <section>
        <h2 className="mb-4 flex items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-amber-400" />
          Señales de manipulación
        </h2>
        {data.manipulation_signals.length === 0 ? (
          <Card className="glass">
            <CardContent className="pt-6 text-sm text-muted-foreground">
              ✓ No se detectaron señales de manipulación significativas en el contenido original.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {data.manipulation_signals.map((s) => (
              <ManipulationSignalCard key={s.id} signal={s} />
            ))}
          </div>
        )}
      </section>

      {/* Input original */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Quote className="h-4 w-4" />
            Contenido analizado
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-muted/50 p-4 text-sm leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap">
            {data.input_normalized ?? data.input_raw}
          </div>
          {data.source_url && (
            <a
              href={data.source_url}
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
            Revisa siempre las fuentes citadas. Si las fuentes se contradicen, lee ambos lados.
            Las señales de manipulación señalan técnicas formales del texto, no significan que el contenido sea falso.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ icon, value, label }: { icon: React.ReactNode; value: number; label: string }) {
  return (
    <div className="rounded-lg bg-muted/40 p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
        {icon} {label}
      </div>
      <p className="text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}
