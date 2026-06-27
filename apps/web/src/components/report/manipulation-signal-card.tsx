"use client";

import { AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import type { ManipulationSignal } from "@/lib/api/verifications";

const SEVERITY_STYLES = {
  low: "text-tier-3 border-tier-3/40 bg-tier-3/10",
  medium: "text-amber-400 border-amber-500/40 bg-amber-500/10",
  high: "text-destructive border-destructive/40 bg-destructive/10",
};

interface Props {
  signal: ManipulationSignal;
}

export function ManipulationSignalCard({ signal }: Props) {
  return (
    <div className={cn(
      "rounded-lg border p-4",
      SEVERITY_STYLES[signal.severity],
    )}>
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <h4 className="font-semibold text-foreground">{signal.signal_type_label}</h4>
            <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
              {signal.severity_label}
            </Badge>
          </div>
          <p className="text-sm text-foreground/85 leading-relaxed">{signal.explanation}</p>
          {signal.evidence_passage && (
            <blockquote className="mt-3 text-xs border-l-2 border-current/30 pl-3 italic text-foreground/70">
              "{signal.evidence_passage}"
            </blockquote>
          )}
        </div>
      </div>
    </div>
  );
}
