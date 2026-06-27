import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "Evidence AI — Verificación de evidencia asistida por IA",
  description:
    "Pega una noticia, URL o transcript. Recolectamos evidencia de fuentes independientes, " +
    "comparamos, calculamos confianza y explicamos por qué. Nunca decimos qué es 'verdadero'.",
  openGraph: {
    title: "Evidence AI",
    description: "Verificación de evidencia asistida por IA. Transparente, didáctica, open source.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark" suppressHydrationWarning>
      <body className={`${inter.variable} ${mono.variable} font-sans antialiased`}>
        <div className="relative flex min-h-screen flex-col">
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
