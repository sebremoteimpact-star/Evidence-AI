"use client";

import Link from "next/link";
import { Sparkles, History, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

// Modo invitado — sin botón de logout
export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/60 bg-background/80 backdrop-blur">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/verificar" className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">Evidence AI</span>
        </Link>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/verificar"><Search className="h-4 w-4" /> Verificar</Link>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/historial"><History className="h-4 w-4" /> Historial</Link>
          </Button>
        </div>
      </div>
    </nav>
  );
}
