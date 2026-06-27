import Link from "next/link";
import { ArrowRight, ShieldCheck, Search, Scale, Sparkles, BookOpen, GitCompare } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="relative">
      {/* Glow de fondo */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-[800px] h-[800px] rounded-full
                        bg-primary/10 blur-[120px]" />
      </div>

      <nav className="container flex items-center justify-between py-6">
        <Link href="/" className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">Evidence AI</span>
        </Link>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/login">Iniciar sesión</Link>
          </Button>
          <Button variant="gradient" size="sm" asChild>
            <Link href="/registro">Crear cuenta gratis</Link>
          </Button>
        </div>
      </nav>

      <section className="container py-20 md:py-32 text-center max-w-4xl">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 rounded-full
                        border border-border bg-card/50 text-xs text-muted-foreground">
          <span className="size-1.5 rounded-full bg-tier-1 animate-pulse-soft" />
          Open source · Gratis · Sin tracking
        </div>

        <h1 className="text-balance mb-6">
          La evidencia importa más que <br />
          <span className="bg-gradient-to-r from-primary to-amber-400 bg-clip-text text-transparent">
            la opinión.
          </span>
        </h1>

        <p className="mx-auto max-w-2xl text-lg text-muted-foreground mb-10 leading-relaxed">
          Pega una noticia, URL, post o transcript. Recolectamos evidencia de fuentes
          independientes, comparamos, calculamos confianza y te explicamos por qué.
          <br />
          <span className="text-foreground font-medium mt-2 inline-block">
            Nunca decimos qué es "verdadero". Decimos qué dice la evidencia.
          </span>
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button variant="gradient" size="xl" asChild>
            <Link href="/verificar">
              Verificar una noticia <ArrowRight className="h-5 w-5" />
            </Link>
          </Button>
          <Button variant="outline" size="xl" asChild>
            <Link href="https://github.com/evidence-ai" target="_blank">
              Ver el código
            </Link>
          </Button>
        </div>
      </section>

      <section className="container py-20 grid md:grid-cols-3 gap-6">
        <FeatureCard
          icon={<Search className="h-6 w-6 text-tier-1" />}
          title="Búsqueda multi-fuente"
          desc="Consultamos PubMed, CrossRef, organismos internacionales, fact-checkers y prensa profesional, no una sola fuente."
        />
        <FeatureCard
          icon={<Scale className="h-6 w-6 text-tier-2" />}
          title="Jerarquía de evidencia"
          desc="Rankeamos cada fuente por transparencia metodológica e independencia. Los papers peer-reviewed pesan más que un blog."
        />
        <FeatureCard
          icon={<GitCompare className="h-6 w-6 text-tier-3" />}
          title="Contradicciones explícitas"
          desc="Si las fuentes se contradicen, te lo decimos. Mostramos ambos lados con citas exactas, no las ocultamos."
        />
        <FeatureCard
          icon={<BookOpen className="h-6 w-6 text-tier-4" />}
          title="Detectores didácticos"
          desc="Identificamos clickbait, propaganda, estadísticas manipuladas y lenguaje emocional — y explicamos cómo reconocerlos."
        />
        <FeatureCard
          icon={<ShieldCheck className="h-6 w-6 text-tier-5" />}
          title="Score auditable"
          desc="El score de confianza se desglosa por factor. Sin caja negra. Cada número se puede inspeccionar y reproducir."
        />
        <FeatureCard
          icon={<Sparkles className="h-6 w-6 text-tier-6" />}
          title="Lenguaje calibrado"
          desc="'La evidencia apoya', 'la evidencia contradice', 'evidencia insuficiente'. Jamás 'verdadero' o 'falso'."
        />
      </section>

      <section className="container py-20 max-w-4xl">
        <div className="glass p-8 md:p-12 rounded-2xl text-center">
          <h2 className="mb-4">Por qué importa</h2>
          <p className="text-muted-foreground leading-relaxed text-lg">
            Un fact-checker que solo dice "verdadero/falso" repite el problema de los medios
            que intenta criticar: pide que le creas. Evidence AI hace lo opuesto:
            <strong className="text-foreground"> te da las fuentes, te muestra el desacuerdo,
            te enseña a evaluar tú.</strong>
          </p>
        </div>
      </section>

      <footer className="container py-10 text-center text-sm text-muted-foreground">
        <p>
          Evidence AI · MIT License · Construido con Claude, Next.js y FastAPI.
        </p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="glass p-6 hover:border-primary/40 transition-colors">
      <div className="mb-4 inline-flex p-3 rounded-lg bg-muted">{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </div>
  );
}
