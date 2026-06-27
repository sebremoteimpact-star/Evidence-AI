"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown, CheckCircle2, XCircle, HelpCircle, Info,
  ThumbsUp, ThumbsDown, AlertTriangle,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EvidenceCard } from "./evidence-card";
import { cn } from "@/lib/utils/cn";
import type { Claim, Verdict } from "@/lib/api/verifications";

const VERDICT_ICONS: Record<Verdict, { icon: React.ReactNode; cls: string }> = {
  strongly_supported:    { icon: <CheckCircle2 className="h-4 w-4" />, cls: "text-tier-1" },
  supported:             { icon: <ThumbsUp className="h-4 w-4" />,     cls: "text-tier-1" },
  mixed:                 { icon: <AlertTriangle className="h-4 w-4" />, cls: "text-amber-400" },
  contradicted:          { icon: <ThumbsDown className="h-4 w-4" />,   cls: "text-destructive" },
  strongly_contradicted: { icon: <XCircle className="h-4 w-4" />,      cls: "text-destructive" },
  insufficient_evidence: { icon: <HelpCircle className="h-4 w-4" />,   cls: "text-muted-foreground" },
};

interface Props {
  claim: Claim;
  index: number;
}

export function ClaimCard({ claim, index }: Props) {
  const [open, setOpen] = useState(index === 0); // primero abierto por defecto

  const v = claim.verdict ? VERDICT_ICONS[claim.verdict] : null;
  const totalEv =
    claim.evidence_supporting.length +
    claim.evidence_contradicting.length +
    claim.evidence_context.length;

  return (
    <Card className="glass overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full text-left p-5 hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-start gap-4">
          <div className="shrink-0 mt-1 flex h-8 w-8 items-center justify-center rounded-full
                          bg-muted text-sm font-semibold tabular-nums">
            {index + 1}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-base leading-snug mb-2">"{claim.text}"</p>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="text-[10px]">
                {claim.claim_type_label}
              </Badge>
              {claim.verdict && v && (
                <Badge
                  variant="outline"
                  className={cn("text-[11px] gap-1 border", v.cls)}
                >
                  {v.icon}
                  {claim.verdict_label}
                </Badge>
              )}
              {claim.confidence_score !== null && (
                <Badge variant="outline" className="text-[11px] tabular-nums">
                  Score {claim.confidence_score}/100
                </Badge>
              )}
              {totalEv > 0 && (
                <span className="text-xs text-muted-foreground">
                  {claim.evidence_supporting.length > 0 && (
                    <span className="text-stance-supports">✓ {claim.evidence_supporting.length}</span>
                  )}
                  {claim.evidence_contradicting.length > 0 && (
                    <span className="text-stance-contradicts ml-2">
                      ✗ {claim.evidence_contradicting.length}
                    </span>
                  )}
                  {claim.evidence_context.length > 0 && (
                    <span className="text-stance-context ml-2">
                      ⓘ {claim.evidence_context.length}
                    </span>
                  )}
                </span>
              )}
            </div>
          </div>
          <ChevronDown
            className={cn("h-5 w-5 text-muted-foreground transition-transform shrink-0 mt-2",
                         open && "rotate-180")}
          />
        </div>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="border-t border-border px-5 py-4 space-y-4">
              {claim.confidence_factors && claim.confidence_factors.length > 0 && (
                <div>
                  <h4 className="text-xs uppercase tracking-wider text-muted-foreground font-medium mb-2">
                    Desglose del score
                  </h4>
                  <div className="space-y-2">
                    {claim.confidence_factors.map((f) => (
                      <div key={f.name} className="text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium capitalize">{f.name.replace(/_/g, " ")}</span>
                          <span className="tabular-nums text-muted-foreground">
                            {(f.value * 100).toFixed(0)}% × peso {(f.weight * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary/70 rounded-full"
                            style={{ width: `${f.value * 100}%` }}
                          />
                        </div>
                        <p className="text-muted-foreground mt-1">{f.explanation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {claim.evidence_supporting.length > 0 && (
                <EvidenceSection
                  title="Evidencia que apoya"
                  icon={<CheckCircle2 className="h-4 w-4 text-stance-supports" />}
                  items={claim.evidence_supporting}
                />
              )}
              {claim.evidence_contradicting.length > 0 && (
                <EvidenceSection
                  title="Evidencia que contradice"
                  icon={<XCircle className="h-4 w-4 text-stance-contradicts" />}
                  items={claim.evidence_contradicting}
                />
              )}
              {claim.evidence_context.length > 0 && (
                <EvidenceSection
                  title="Contexto"
                  icon={<Info className="h-4 w-4 text-stance-context" />}
                  items={claim.evidence_context}
                />
              )}

              {totalEv === 0 && (
                <div className="text-sm text-muted-foreground italic flex items-center gap-2">
                  <HelpCircle className="h-4 w-4" />
                  No se encontró evidencia relevante para esta afirmación.
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function EvidenceSection({
  title, icon, items,
}: { title: string; icon: React.ReactNode; items: Claim["evidence_supporting"] }) {
  return (
    <div>
      <h4 className="text-xs uppercase tracking-wider text-muted-foreground font-medium mb-2 flex items-center gap-2">
        {icon} {title} <span className="tabular-nums">({items.length})</span>
      </h4>
      <div className="grid gap-2 md:grid-cols-2">
        {items.map((e) => <EvidenceCard key={e.id} evidence={e} />)}
      </div>
    </div>
  );
}
