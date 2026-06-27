"""Esquema inicial — users, sources, verifications, claims, evidence, signals, events, reports, audit_log.

Revision ID: 20260626_0001
Revises:
Create Date: 2026-06-26 12:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "20260626_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ─────────────────────────────────────────────
    # Extensiones (idempotente — el init SQL ya las crea)
    # ─────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")  # para gen_random_uuid()

    # ─────────────────────────────────────────────
    # ENUMs
    # ─────────────────────────────────────────────
    source_tier = postgresql.ENUM("1", "2", "3", "4", "5", "6", name="source_tier")
    source_type = postgresql.ENUM(
        "academic_database", "academic_index", "academic_api", "academic_metadata",
        "journal", "preprint", "court", "legislature", "government", "open_data",
        "national_statistics", "central_bank", "international_org", "data_platform",
        "factcheck", "university", "research_institute", "think_tank",
        "news_agency", "news", "other",
        name="source_type",
    )
    claim_type = postgresql.ENUM(
        "factual", "opinion", "prediction", "normative", "unverifiable",
        name="claim_type",
    )
    stance = postgresql.ENUM(
        "supports", "contradicts", "context", "unrelated", name="stance"
    )
    input_type_enum = postgresql.ENUM(
        "text", "url", "youtube", "upload_video", "upload_pdf", "social_post",
        name="input_type",
    )
    verification_status = postgresql.ENUM(
        "pending", "ingesting", "extracting_claims", "detecting_manipulation",
        "searching_evidence", "ranking_evidence", "reasoning", "composing_report",
        "completed", "failed", "cancelled",
        name="verification_status",
    )
    manipulation_type = postgresql.ENUM(
        "emotional_language", "clickbait", "propaganda", "misleading_headline",
        "manipulated_stats", "context_manipulation", "ai_generated", "deepfake_indicator",
        name="manipulation_type",
    )
    signal_severity = postgresql.ENUM("low", "medium", "high", name="signal_severity")
    verdict = postgresql.ENUM(
        "strongly_supported", "supported", "mixed", "contradicted",
        "strongly_contradicted", "insufficient_evidence",
        name="verdict",
    )

    bind = op.get_bind()
    for enum in (source_tier, source_type, claim_type, stance, input_type_enum,
                 verification_status, manipulation_type, signal_severity, verdict):
        enum.create(bind, checkfirst=True)

    # ─────────────────────────────────────────────
    # users
    # ─────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("oauth_provider", sa.String(50)),
        sa.Column("oauth_subject", sa.String(255)),
        sa.Column("locale", sa.String(5), nullable=False, server_default="es"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_oauth_subject", "users", ["oauth_subject"])

    # ─────────────────────────────────────────────
    # sources
    # ─────────────────────────────────────────────
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("canonical_url", sa.Text, nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("tier", postgresql.ENUM(name="source_tier", create_type=False), nullable=False),
        sa.Column("source_type", postgresql.ENUM(name="source_type", create_type=False), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("language", sa.String(5)),
        sa.Column("methodology_notes", sa.Text),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_sources"),
        sa.UniqueConstraint("canonical_url", name="uq_sources_canonical_url"),
    )
    op.create_index("ix_sources_canonical_url", "sources", ["canonical_url"])
    op.create_index("ix_sources_domain", "sources", ["domain"])
    op.create_index("ix_sources_tier", "sources", ["tier"])
    op.create_index("ix_sources_content_hash", "sources", ["content_hash"])

    # ─────────────────────────────────────────────
    # verifications
    # ─────────────────────────────────────────────
    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("input_type", postgresql.ENUM(name="input_type", create_type=False), nullable=False),
        sa.Column("input_raw", sa.Text, nullable=False),
        sa.Column("input_normalized", sa.Text),
        sa.Column("source_url", sa.Text),
        sa.Column("language", sa.String(5)),
        sa.Column("status", postgresql.ENUM(name="verification_status", create_type=False),
                  nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_verifications_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_verifications"),
    )
    op.create_index("ix_verifications_user_id", "verifications", ["user_id"])
    op.create_index("ix_verifications_status", "verifications", ["status"])
    op.create_index("ix_verifications_created_at", "verifications", ["created_at"])

    # ─────────────────────────────────────────────
    # claims
    # ─────────────────────────────────────────────
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("claim_type", postgresql.ENUM(name="claim_type", create_type=False), nullable=False),
        sa.Column("context", sa.Text),
        sa.Column("keywords", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"],
                                name="fk_claims_verification_id_verifications", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_claims"),
    )
    op.create_index("ix_claims_verification_id", "claims", ["verification_id"])
    op.create_index("ix_claims_claim_type", "claims", ["claim_type"])

    # ─────────────────────────────────────────────
    # evidence (con embedding vector y índice HNSW)
    # ─────────────────────────────────────────────
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("passage", sa.Text, nullable=False),
        sa.Column("passage_hash", sa.Text, nullable=False),
        sa.Column("stance", postgresql.ENUM(name="stance", create_type=False), nullable=False),
        sa.Column("relevance_score", sa.Float, nullable=False),
        sa.Column("embedding", Vector(1024)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], name="fk_evidence_claim_id_claims", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_evidence_source_id_sources", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_evidence"),
    )
    op.create_index("ix_evidence_claim_id", "evidence", ["claim_id"])
    op.create_index("ix_evidence_source_id", "evidence", ["source_id"])
    op.create_index("ix_evidence_stance", "evidence", ["stance"])
    op.create_index("ix_evidence_passage_hash", "evidence", ["passage_hash"])

    # Índice HNSW para búsqueda vectorial aproximada (cosine distance)
    op.execute(
        "CREATE INDEX ix_evidence_embedding_hnsw ON evidence "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )

    # ─────────────────────────────────────────────
    # manipulation_signals
    # ─────────────────────────────────────────────
    op.create_table(
        "manipulation_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", postgresql.ENUM(name="manipulation_type", create_type=False), nullable=False),
        sa.Column("severity", postgresql.ENUM(name="signal_severity", create_type=False), nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("evidence_passage", sa.Text),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"],
                                name="fk_manipulation_signals_verification_id_verifications",
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_manipulation_signals"),
    )
    op.create_index("ix_manipulation_signals_verification_id", "manipulation_signals", ["verification_id"])

    # ─────────────────────────────────────────────
    # verification_events (SSE replay)
    # ─────────────────────────────────────────────
    op.create_table(
        "verification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"],
                                name="fk_verification_events_verification_id_verifications",
                                ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_verification_events"),
    )
    op.create_index("ix_verification_events_verification_id", "verification_events", ["verification_id"])
    op.create_index("ix_verification_events_event_type", "verification_events", ["event_type"])
    op.create_index("ix_verification_events_created_at", "verification_events", ["created_at"])

    # ─────────────────────────────────────────────
    # reports
    # ─────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("executive_conclusion", sa.Text, nullable=False),
        sa.Column("confidence_value", sa.Integer, nullable=False),
        sa.Column("verdict", postgresql.ENUM(name="verdict", create_type=False), nullable=False),
        sa.Column("confidence_breakdown", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidence_value >= 0 AND confidence_value <= 100", name="ck_reports_confidence_range"),
        sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"],
                                name="fk_reports_verification_id_verifications", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
        sa.UniqueConstraint("verification_id", name="uq_reports_verification_id"),
    )

    # ─────────────────────────────────────────────
    # audit_log (sin FKs CASCADE — sobrevive borrado)
    # ─────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("verification_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("prompt_hash", sa.String(64)),
        sa.Column("model_used", sa.String(100)),
        sa.Column("tokens_input", sa.Integer),
        sa.Column("tokens_output", sa.Integer),
        sa.Column("cost_estimate_usd", sa.Numeric(10, 6)),
        sa.Column("extra", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("ix_audit_log_verification_id", "audit_log", ["verification_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    # Tablas en orden inverso de dependencias
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_verification_id", table_name="audit_log")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_table("reports")

    op.drop_index("ix_verification_events_created_at", table_name="verification_events")
    op.drop_index("ix_verification_events_event_type", table_name="verification_events")
    op.drop_index("ix_verification_events_verification_id", table_name="verification_events")
    op.drop_table("verification_events")

    op.drop_index("ix_manipulation_signals_verification_id", table_name="manipulation_signals")
    op.drop_table("manipulation_signals")

    op.execute("DROP INDEX IF EXISTS ix_evidence_embedding_hnsw;")
    op.drop_index("ix_evidence_passage_hash", table_name="evidence")
    op.drop_index("ix_evidence_stance", table_name="evidence")
    op.drop_index("ix_evidence_source_id", table_name="evidence")
    op.drop_index("ix_evidence_claim_id", table_name="evidence")
    op.drop_table("evidence")

    op.drop_index("ix_claims_claim_type", table_name="claims")
    op.drop_index("ix_claims_verification_id", table_name="claims")
    op.drop_table("claims")

    op.drop_index("ix_verifications_created_at", table_name="verifications")
    op.drop_index("ix_verifications_status", table_name="verifications")
    op.drop_index("ix_verifications_user_id", table_name="verifications")
    op.drop_table("verifications")

    op.drop_index("ix_sources_content_hash", table_name="sources")
    op.drop_index("ix_sources_tier", table_name="sources")
    op.drop_index("ix_sources_domain", table_name="sources")
    op.drop_index("ix_sources_canonical_url", table_name="sources")
    op.drop_table("sources")

    op.drop_index("ix_users_oauth_subject", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    for enum_name in ("verdict", "signal_severity", "manipulation_type",
                      "verification_status", "input_type", "stance", "claim_type",
                      "source_type", "source_tier"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")
