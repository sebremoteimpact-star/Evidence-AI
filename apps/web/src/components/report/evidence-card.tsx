"use client";

import { ExternalLink } from "lucide-react";
import { SourceTierBadge } from "./source-tier-badge";
import { cn } from "@/lib/utils/cn";
import type { Evidence } from "@/lib/api/verifications";

const STANCE_STYLES = {
  supports: "border-l-stance-supports/60 bg-stance-supports/[0.04]",
  contradicts: "border-l-stance-contradicts/60 bg-stance-contradicts/[0.04]",
  context: "border-l-stance-context/60 bg-stance-context/[0.04]",
  unrelated: "border-l-stance-unrelated/40 bg-stance-unrelated/[0.04]",
};

interface Props {
  evidence: Evidence;
}

export function EvidenceCard({ evidence }: Props) {
  return (
    <div
      className={cn(
        "rounded-md border border-border border-l-4 p-3 transition-colors hover:bg-muted/30",
        STANCE_STYLES[evidence.stance],
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <SourceTierBadge tier={evidence.source.tier as 1 | 2 | 3 | 4 | 5 | 6} />
        <span className="text-[10px] text-muted-foreground tabular-nums shrink-0">
          rel {Math.round(evidence.relevance_score * 100)}%
        </span>
      </div>

      <blockquote className="text-sm leading-relaxed text-foreground/90 mb-3 border-l-2 border-border pl-3 italic">
        "{evidence.passage.length > 320 ? evidence.passage.slice(0, 320) + "…" : evidence.passage}"
      </blockquote>

      <a
        href={evidence.source.canonical_url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline truncate max-w-full"
        title={evidence.source.canonical_url}
      >
        <span className="truncate">
          {evidence.source.title ?? evidence.source.domain}
        </span>
        <ExternalLink className="h-3 w-3 shrink-0" />
      </a>
      {evidence.source.methodology_notes && (
        <p className="text-[11px] text-amber-400 mt-1.5 italic">
          ⓘ {evidence.source.methodology_notes}
        </p>
      )}
    </div>
  );
}
