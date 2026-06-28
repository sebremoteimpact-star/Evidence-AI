import { apiClient } from "./client";

export type InputType = "text" | "url" | "youtube" | "upload_video" | "upload_pdf" | "social_post";

export type VerificationStatus =
  | "pending" | "ingesting" | "extracting_claims" | "detecting_manipulation"
  | "searching_evidence" | "ranking_evidence" | "reasoning" | "composing_report"
  | "completed" | "failed" | "cancelled";

export interface Verification {
  id: string;
  user_id: string;
  input_type: InputType;
  input_raw: string;
  input_normalized: string | null;
  source_url: string | null;
  language: string | null;
  status: VerificationStatus;
  status_label: string;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface VerificationList {
  items: Verification[];
  next_cursor: string | null;
}

export type Stance = "supports" | "contradicts" | "context" | "unrelated";
export type Verdict =
  | "strongly_supported" | "supported" | "mixed"
  | "contradicted" | "strongly_contradicted" | "insufficient_evidence";
export type SourceTier = 1 | 2 | 3 | 4 | 5 | 6;

export interface Source {
  id: string;
  canonical_url: string;
  domain: string;
  title: string | null;
  tier: SourceTier;
  tier_label: string;
  source_type: string;
  source_type_label: string;
  published_at: string | null;
  language: string | null;
  methodology_notes: string | null;
}

export interface Evidence {
  id: string;
  source: Source;
  passage: string;
  stance: Stance;
  stance_label: string;
  relevance_score: number;
  retrieved_at: string;
}

export interface ConfidenceFactor {
  name: string;
  value: number;
  weight: number;
  explanation: string;
}

export interface Claim {
  id: string;
  position: number;
  text: string;
  claim_type: "factual" | "opinion" | "prediction" | "normative" | "unverifiable";
  claim_type_label: string;
  context: string | null;
  keywords: string[];
  evidence_supporting: Evidence[];
  evidence_contradicting: Evidence[];
  evidence_context: Evidence[];
  confidence_score: number | null;
  verdict: Verdict | null;
  verdict_label: string | null;
  confidence_factors: ConfidenceFactor[];
}

export interface ManipulationSignal {
  id: string;
  signal_type: string;
  signal_type_label: string;
  severity: "low" | "medium" | "high";
  severity_label: string;
  explanation: string;
  evidence_passage: string | null;
}

export interface ReportSummary {
  headline: string;
  summary: string;
  executive_conclusion: string;
  confidence_value: number;
  verdict: Verdict;
  verdict_label: string;
  language: string;
  generated_at: string;
}

export interface FullVerification extends Verification {
  input_type_label: string;
  report: ReportSummary | null;
  claims: Claim[];
  manipulation_signals: ManipulationSignal[];
  stats: {
    total_claims: number;
    factual_claims: number;
    total_evidence: number;
    n_supporting: number;
    n_contradicting: number;
    n_context: number;
    unique_domains: number;
    unique_tiers: number;
    manipulation_signals: number;
  };
}

export const verificationsApi = {
  create: (input_type: InputType, input_raw: string) =>
    apiClient.post<Verification>("/api/v1/verifications", { input_type, input_raw }),

  get: (id: string) => apiClient.get<Verification>(`/api/v1/verifications/${id}`),

  getFull: (id: string) => apiClient.get<FullVerification>(`/api/v1/verifications/${id}/full`),

  list: (params?: { limit?: number; cursor?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.cursor) qs.set("cursor", params.cursor);
    const suffix = qs.toString() ? `?${qs}` : "";
    return apiClient.get<VerificationList>(`/api/v1/verifications${suffix}`);
  },
};
