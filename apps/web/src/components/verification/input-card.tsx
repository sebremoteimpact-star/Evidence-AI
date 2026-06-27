"use client";

import { useState } from "react";
import { Link2, FileText, Youtube, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils/cn";
import type { InputType } from "@/lib/api/verifications";

type Mode = "text" | "url" | "youtube";

interface Props {
  onSubmit: (type: InputType, raw: string) => Promise<void>;
  loading?: boolean;
}

export function InputCard({ onSubmit, loading }: Props) {
  const [mode, setMode] = useState<Mode>("text");
  const [value, setValue] = useState("");

  const tabs: { id: Mode; label: string; icon: React.ReactNode; placeholder: string; help: string }[] = [
    {
      id: "text",
      label: "Texto",
      icon: <FileText className="h-4 w-4" />,
      placeholder: "Pega aquí el texto, noticia, post o transcript que quieres verificar...",
      help: "Hasta 50.000 caracteres. Detectamos el idioma automáticamente.",
    },
    {
      id: "url",
      label: "URL",
      icon: <Link2 className="h-4 w-4" />,
      placeholder: "https://ejemplo.com/articulo",
      help: "Extraemos el texto canónico y lo procesamos.",
    },
    {
      id: "youtube",
      label: "YouTube",
      icon: <Youtube className="h-4 w-4" />,
      placeholder: "https://youtube.com/watch?v=...",
      help: "Usamos el transcript del video. Requiere subtítulos disponibles.",
    },
  ];

  const current = tabs.find((t) => t.id === mode)!;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim() || loading) return;
    const type: InputType = mode === "youtube" ? "youtube" : mode === "url" ? "url" : "text";
    await onSubmit(type, value.trim());
  }

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          ¿Qué quieres verificar?
        </CardTitle>
        <CardDescription>
          Te devolvemos un reporte con evidencia de fuentes independientes en ~60 segundos.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-1 p-1 bg-muted rounded-lg mb-4 w-fit">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setMode(t.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all",
                mode === t.id
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "text" ? (
            <Textarea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={current.placeholder}
              maxLength={50000}
              className="min-h-[220px]"
              required
            />
          ) : (
            <Input
              type="url"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={current.placeholder}
              required
            />
          )}

          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">{current.help}</p>
            {mode === "text" && (
              <p className="text-xs text-muted-foreground tabular-nums">
                {value.length.toLocaleString()} / 50.000
              </p>
            )}
          </div>

          <Button type="submit" variant="gradient" size="lg" className="w-full" disabled={loading || !value.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? "Iniciando verificación..." : "Verificar evidencia"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
