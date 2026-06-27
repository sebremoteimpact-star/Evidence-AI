"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, CheckCircle2, AlertTriangle, Search, Brain, FileText,
  Globe, Quote, Loader2, XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils/cn";
import type { StreamEvent } from "@/hooks/use-verification-stream";

interface Props {
  events: StreamEvent[];
  isComplete: boolean;
  isFailed: boolean;
}

const EVENT_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  ingesting:                     { label: "Procesando contenido",          icon: <FileText className="h-4 w-4" />,    color: "text-tier-3" },
  ingested:                      { label: "Contenido extraído",            icon: <CheckCircle2 className="h-4 w-4" />, color: "text-tier-1" },
  manipulation_detection_start:  { label: "Analizando señales de manipulación", icon: <AlertTriangle className="h-4 w-4" />, color: "text-amber-400" },
  manipulation_detected:         { label: "Análisis de manipulación completo", icon: <AlertTriangle className="h-4 w-4" />, color: "text-amber-400" },
  claims_extraction_start:       { label: "Extrayendo afirmaciones",       icon: <Brain className="h-4 w-4" />,        color: "text-tier-4" },
  claims_extracted:              { label: "Afirmaciones identificadas",    icon: <CheckCircle2 className="h-4 w-4" />, color: "text-tier-1" },
  claim_processing_start:        { label: "Verificando afirmación",        icon: <Brain className="h-4 w-4" />,        color: "text-tier-2" },
  queries_generated:             { label: "Queries de búsqueda generadas", icon: <Search className="h-4 w-4" />,       color: "text-tier-3" },
  sources_found:                 { label: "Fuentes encontradas",           icon: <Globe className="h-4 w-4" />,        color: "text-tier-2" },
  claim_no_evidence:             { label: "Sin evidencia para esta afirmación", icon: <AlertTriangle className="h-4 w-4" />, color: "text-amber-400" },
  claim_completed:               { label: "Afirmación evaluada",           icon: <Quote className="h-4 w-4" />,        color: "text-tier-1" },
  composing_report:              { label: "Componiendo reporte",           icon: <Sparkles className="h-4 w-4" />,     color: "text-primary" },
  completed:                     { label: "Verificación completa",         icon: <CheckCircle2 className="h-4 w-4" />, color: "text-tier-1" },
  failed:                        { label: "Error",                         icon: <XCircle className="h-4 w-4" />,      color: "text-destructive" },
};

export function ProgressTimeline({ events, isComplete, isFailed }: Props) {
  const visible = events.filter((e) => e.type !== "ping" && e.type !== "end");
  const last = visible[visible.length - 1];

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {isComplete ? (
            <CheckCircle2 className="h-5 w-5 text-tier-1" />
          ) : isFailed ? (
            <XCircle className="h-5 w-5 text-destructive" />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          )}
          {isComplete ? "Verificación completada" : isFailed ? "Verificación falló" : "Procesando en vivo..."}
        </CardTitle>
        {last && !isComplete && !isFailed && (
          <p className="text-sm text-muted-foreground">
            {EVENT_META[last.type]?.label ?? last.type}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Línea vertical */}
          <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border" />

          <ul className="space-y-3">
            <AnimatePresence initial={false}>
              {visible.map((event, idx) => {
                const meta = EVENT_META[event.type];
                if (!meta) return null;
                const isLast = idx === visible.length - 1 && !isComplete && !isFailed;
                return (
                  <motion.li
                    key={`${event.seq}-${event.type}`}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.25 }}
                    className="relative flex items-start gap-3 pl-1"
                  >
                    <div
                      className={cn(
                        "relative z-10 flex h-8 w-8 items-center justify-center rounded-full",
                        "bg-card border border-border",
                        meta.color,
                        isLast && "ring-2 ring-primary/40 animate-pulse-soft",
                      )}
                    >
                      {meta.icon}
                    </div>
                    <div className="flex-1 pt-1">
                      <p className="text-sm font-medium">{meta.label}</p>
                      {renderPayloadHint(event)}
                    </div>
                    <time className="text-xs text-muted-foreground pt-1.5 tabular-nums">
                      {new Date(event.ts).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                    </time>
                  </motion.li>
                );
              })}
            </AnimatePresence>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

function renderPayloadHint(event: StreamEvent) {
  const p = event.payload;
  switch (event.type) {
    case "ingested":
      return (
        <div className="flex flex-wrap gap-2 mt-1">
          <Badge variant="outline">{p.chars?.toLocaleString()} caracteres</Badge>
          {p.language && <Badge variant="outline">Idioma: {p.language}</Badge>}
        </div>
      );
    case "claims_extracted":
      return (
        <p className="text-xs text-muted-foreground mt-1">
          {p.count} afirmaciones identificadas
        </p>
      );
    case "queries_generated":
      return (
        <div className="flex flex-wrap gap-1 mt-1">
          {p.queries?.slice(0, 3).map((q: string, i: number) => (
            <Badge key={i} variant="secondary" className="font-mono text-[10px]">
              {q.length > 50 ? q.slice(0, 50) + "…" : q}
            </Badge>
          ))}
        </div>
      );
    case "sources_found":
      return (
        <p className="text-xs text-muted-foreground mt-1">
          {p.count} fuentes en {p.domains?.length} dominios únicos
        </p>
      );
    case "claim_completed":
      return (
        <div className="flex flex-wrap gap-2 mt-1">
          <Badge variant="outline">Score {p.score}/100</Badge>
          {p.n_supports > 0 && (
            <Badge className="stance-supports">✓ {p.n_supports} apoyan</Badge>
          )}
          {p.n_contradicts > 0 && (
            <Badge className="stance-contradicts">✗ {p.n_contradicts} contradicen</Badge>
          )}
          {p.n_context > 0 && (
            <Badge className="stance-context">i {p.n_context} contexto</Badge>
          )}
        </div>
      );
    case "manipulation_detected":
      if (p.count === 0) return <p className="text-xs text-tier-1 mt-1">Sin señales detectadas</p>;
      return (
        <p className="text-xs text-amber-400 mt-1">
          {p.count} {p.count === 1 ? "señal detectada" : "señales detectadas"}
        </p>
      );
    case "failed":
      return <p className="text-xs text-destructive mt-1">{p.error}</p>;
    default:
      return null;
  }
}
