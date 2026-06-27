"use client";

import { useEffect, useRef, useState } from "react";
import { apiClient, tokenStorage } from "@/lib/api/client";

export type StreamEventType =
  | "ingesting" | "ingested"
  | "manipulation_detection_start" | "manipulation_detected"
  | "claims_extraction_start" | "claims_extracted"
  | "claim_processing_start" | "queries_generated"
  | "sources_found" | "claim_no_evidence" | "claim_completed"
  | "composing_report" | "completed" | "failed" | "ping" | "end";

export interface StreamEvent {
  type: StreamEventType;
  payload: Record<string, any>;
  ts: string;
  seq: number;
}

export interface UseVerificationStream {
  events: StreamEvent[];
  status: "connecting" | "open" | "closed" | "error";
  isComplete: boolean;
  isFailed: boolean;
}

/**
 * Hook que se conecta al SSE de una verificación y mantiene la lista
 * acumulada de eventos. Auto-reconecta usando `since` para no perder eventos.
 */
export function useVerificationStream(verificationId: string | null): UseVerificationStream {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<UseVerificationStream["status"]>("connecting");
  const seqRef = useRef(0);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!verificationId) return;

    const token = tokenStorage.get();
    if (!token) {
      setStatus("error");
      return;
    }

    // EventSource no soporta headers — usamos query param para auth.
    // En producción esto debería ir por cookie httpOnly, pero para MVP es aceptable.
    const url = `${apiClient.apiUrl}/api/v1/stream/${verificationId}?since=${seqRef.current}`;

    // Pasamos token en query string (alternativa: usar fetch + ReadableStream)
    // Por ahora EventSource estándar; en Fase 14 migramos a fetch-based SSE para meter el header.
    const es = new EventSource(`${url}&token=${encodeURIComponent(token)}`);
    sourceRef.current = es;
    setStatus("open");

    const handleMessage = (type: StreamEventType) => (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        seqRef.current += 1;
        setEvents((prev) => [
          ...prev,
          { type, payload: data.payload ?? {}, ts: data.ts ?? new Date().toISOString(), seq: seqRef.current },
        ]);
        if (type === "completed" || type === "failed" || type === "end") {
          es.close();
          setStatus("closed");
        }
      } catch {
        // ignore malformed
      }
    };

    // Registramos handlers para cada tipo de evento que el backend emite
    const types: StreamEventType[] = [
      "ingesting", "ingested",
      "manipulation_detection_start", "manipulation_detected",
      "claims_extraction_start", "claims_extracted",
      "claim_processing_start", "queries_generated",
      "sources_found", "claim_no_evidence", "claim_completed",
      "composing_report", "completed", "failed", "ping", "end",
    ];
    types.forEach((t) => es.addEventListener(t, handleMessage(t) as EventListener));

    es.onerror = () => {
      setStatus("error");
      // EventSource intentará reconectar automáticamente
    };

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, [verificationId]);

  const isComplete = events.some((e) => e.type === "completed");
  const isFailed = events.some((e) => e.type === "failed");

  return { events, status, isComplete, isFailed };
}
