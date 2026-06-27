"use client";

import { Award, Building2, Globe2, ShieldCheck, GraduationCap, Newspaper } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface Props {
  tier: 1 | 2 | 3 | 4 | 5 | 6;
  className?: string;
  showLabel?: boolean;
}

const TIER_META = {
  1: { label: "Peer-reviewed",       icon: <Award className="h-3 w-3" />,         className: "tier-1" },
  2: { label: "Oficial",             icon: <Building2 className="h-3 w-3" />,     className: "tier-2" },
  3: { label: "Organismo internacional", icon: <Globe2 className="h-3 w-3" />,    className: "tier-3" },
  4: { label: "Fact-checker",        icon: <ShieldCheck className="h-3 w-3" />,   className: "tier-4" },
  5: { label: "Académico",           icon: <GraduationCap className="h-3 w-3" />, className: "tier-5" },
  6: { label: "Periodismo",          icon: <Newspaper className="h-3 w-3" />,     className: "tier-6" },
} as const;

export function SourceTierBadge({ tier, showLabel = true, className }: Props) {
  const meta = TIER_META[tier];
  return (
    <span
      className={cn("tier-badge", meta.className, className)}
      title={meta.label}
    >
      {meta.icon}
      {showLabel && meta.label}
    </span>
  );
}
