"use client";

import { motion } from "framer-motion";
import {
  CheckCircle2, AlertTriangle, XCircle, HelpCircle,
  ThumbsUp, ThumbsDown,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

type Verdict =
  | "strongly_supported" | "supported" | "mixed"
  | "contradicted" | "strongly_contradicted" | "insufficient_evidence";

interface Props {
  verdict: Verdict;
  className?: string;
}

const VERDICT_CONFIG: Record<Verdict, {
  label: string;
  detail: string;
  icon: React.ReactNode;
  bg: string;
  text: string;
  border: string;
}> = {
  strongly_supported: {
    label: "La evidencia apoya fuertemente",
    detail: "Múltiples fuentes independientes de alta calidad respaldan esta afirmación de forma consistente.",
    icon: <CheckCircle2 className="h-8 w-8" />,
    bg: "bg-tier-1/10",
    text: "text-tier-1",
    border: "border-tier-1/40",
  },
  supported: {
    label: "La evidencia apoya",
    detail: "Las fuentes consultadas tienden a respaldar esta afirmación, aunque la evidencia no es abrumadora.",
    icon: <ThumbsUp className="h-8 w-8" />,
    bg: "bg-tier-1/10",
    text: "text-tier-1",
    border: "border-tier-1/40",
  },
  mixed: {
    label: "La evidencia es mixta",
    detail: "Hay fuentes que apoyan y fuentes que contradicen esta afirmación. Lee ambos lados antes de concluir.",
    icon: <AlertTriangle className="h-8 w-8" />,
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/40",
  },
  contradicted: {
    label: "La evidencia contradice",
    detail: "Las fuentes consultadas tienden a contradecir esta afirmación.",
    icon: <ThumbsDown className="h-8 w-8" />,
    bg: "bg-destructive/10",
    text: "text-destructive",
    border: "border-destructive/40",
  },
  strongly_contradicted: {
    label: "La evidencia contradice fuertemente",
    detail: "Múltiples fuentes independientes de alta calidad contradicen esta afirmación de forma consistente.",
    icon: <XCircle className="h-8 w-8" />,
    bg: "bg-destructive/10",
    text: "text-destructive",
    border: "border-destructive/40",
  },
  insufficient_evidence: {
    label: "Evidencia insuficiente",
    detail: "No se encontraron suficientes fuentes de calidad para tomar una postura clara sobre esta afirmación.",
    icon: <HelpCircle className="h-8 w-8" />,
    bg: "bg-muted",
    text: "text-muted-foreground",
    border: "border-border",
  },
};

export function VerdictBanner({ verdict, className }: Props) {
  const cfg = VERDICT_CONFIG[verdict];
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn(
        "flex items-start gap-4 p-6 rounded-xl border-2",
        cfg.bg, cfg.border, className,
      )}
    >
      <div className={cn("shrink-0 mt-1", cfg.text)}>{cfg.icon}</div>
      <div className="flex-1">
        <h3 className={cn("text-xl font-semibold mb-1", cfg.text)}>{cfg.label}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">{cfg.detail}</p>
        <p className="text-xs text-muted-foreground mt-3 italic">
          Este sistema nunca declara algo como "verdadero" o "falso" — describe el peso de la evidencia recolectada.
        </p>
      </div>
    </motion.div>
  );
}
