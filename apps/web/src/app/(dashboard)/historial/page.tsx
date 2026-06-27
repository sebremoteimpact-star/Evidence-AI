"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { History, Loader2, FileText, Link2, Youtube, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { verificationsApi, type Verification } from "@/lib/api/verifications";

const TYPE_ICONS = {
  text: <FileText className="h-4 w-4" />,
  url: <Link2 className="h-4 w-4" />,
  youtube: <Youtube className="h-4 w-4" />,
  upload_video: <Youtube className="h-4 w-4" />,
  upload_pdf: <FileText className="h-4 w-4" />,
  social_post: <FileText className="h-4 w-4" />,
};

export default function HistorialPage() {
  const [items, setItems] = useState<Verification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    verificationsApi.list({ limit: 30 })
      .then((res) => setItems(res.items))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="flex items-center gap-3 mb-2">
          <History className="h-8 w-8 text-primary" />
          Historial de verificaciones
        </h1>
        <p className="text-muted-foreground">
          Tus {items.length} verificaciones más recientes.
        </p>
      </div>

      {items.length === 0 ? (
        <Card className="glass">
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground mb-4">Aún no has verificado nada.</p>
            <Button variant="gradient" asChild>
              <Link href="/verificar">Verificar lo primero</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((v) => (
            <Link key={v.id} href={`/reportes/${v.id}`}>
              <Card className="glass hover:border-primary/40 transition-colors cursor-pointer">
                <CardContent className="pt-5 pb-5">
                  <div className="flex items-start gap-4">
                    <div className="shrink-0 p-2 rounded-lg bg-muted">
                      {TYPE_ICONS[v.input_type as keyof typeof TYPE_ICONS] ?? <FileText className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">
                        {v.source_url ?? (v.input_raw.slice(0, 100) + (v.input_raw.length > 100 ? "..." : ""))}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        <StatusBadge status={v.status} label={v.status_label} />
                        {v.language && <Badge variant="outline" className="text-xs">{v.language}</Badge>}
                        <span className="text-xs text-muted-foreground">
                          {new Date(v.created_at).toLocaleString("es")}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status, label }: { status: string; label: string }) {
  if (status === "completed") return <Badge variant="success">{label}</Badge>;
  if (status === "failed") return <Badge variant="danger">{label}</Badge>;
  if (status === "cancelled") return <Badge variant="outline">{label}</Badge>;
  return (
    <Badge variant="warning" className="gap-1">
      <Loader2 className="h-3 w-3 animate-spin" />
      {label}
    </Badge>
  );
}
