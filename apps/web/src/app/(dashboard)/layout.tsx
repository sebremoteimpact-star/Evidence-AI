"use client";

import { Navbar } from "@/components/layout/navbar";

// Modo invitado activo — sin auth guard. El backend tiene un usuario
// "guest" compartido que recibe todas las verificaciones cuando no hay JWT.
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 container py-8">{children}</main>
    </div>
  );
}
