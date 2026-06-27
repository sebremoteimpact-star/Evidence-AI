"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

interface Props {
  value: number; // 0-100
  size?: "sm" | "lg";
  label?: string;
}

/**
 * Medidor circular animado de confianza.
 * Color dinámico según el score.
 */
export function ConfidenceMeter({ value, size = "lg", label }: Props) {
  const v = Math.max(0, Math.min(100, value));
  const dim = size === "lg" ? 180 : 100;
  const stroke = size === "lg" ? 14 : 8;
  const radius = (dim - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (v / 100) * circumference;

  const color =
    v >= 75 ? "var(--tier-1)" :
    v >= 50 ? "var(--tier-3)" :
    v >= 25 ? "#f59e0b" :
    "var(--destructive)";

  return (
    <div className="inline-flex flex-col items-center gap-2">
      <div className="relative">
        <svg width={dim} height={dim} className="-rotate-90">
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            stroke="hsl(var(--muted))"
            strokeWidth={stroke}
            fill="none"
          />
          <motion.circle
            cx={dim / 2}
            cy={dim / 2}
            r={radius}
            stroke={`hsl(${color})`}
            strokeWidth={stroke}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.4, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 8px hsl(${color} / 0.4))` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className={cn(
              "font-semibold tabular-nums",
              size === "lg" ? "text-5xl" : "text-2xl",
            )}
            style={{ color: `hsl(${color})` }}
          >
            {v}
          </motion.div>
          <span className={cn(
            "text-muted-foreground font-medium",
            size === "lg" ? "text-sm" : "text-xs",
          )}>
            /100
          </span>
        </div>
      </div>
      {label && <p className="text-xs text-muted-foreground text-center">{label}</p>}
    </div>
  );
}
