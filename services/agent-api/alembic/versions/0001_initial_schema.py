from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def pk_type():
    return sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def timestamps() -> list[sa.Column]:
    update_default = sa.text("CURRENT_TIMESTAMP")
    if op.get_context().dialect.name == "mysql":
        update_default = sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    return [
        sa.Column("create_time", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "update_time",
            sa.DateTime(),
            nullable=False,
            server_default=update_default,
        ),
        sa.Column("deleted", sa.Integer(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    op.create_table(
        "dialogue_session_ledger",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(128), nullable=False),
        sa.Column("visitor_id", sa.String(128)),
        sa.Column("title", sa.String(255)),
        sa.Column("status", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latest_request_id", sa.String(128)),
        sa.Column("latest_query_text", sa.Text()),
        sa.Column("latest_summary_text", sa.Text()),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("finished_run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("last_active_at", sa.DateTime()),
        *timestamps(),
        sa.UniqueConstraint("session_id", name="uk_dialogue_session_session_id"),
    )
    op.create_table(
        "dialogue_run_ledger",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("run_uid", sa.String(128), nullable=False),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=False),
        sa.Column("visitor_id", sa.String(128)),
        sa.Column("entry_agent", sa.String(64), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("query_text", sa.Text()),
        sa.Column("final_summary_text", sa.Text()),
        sa.Column("llm_call_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_call_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("artifact_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt_tokens_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(128)),
        sa.Column("error_msg", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("duration_ms", sa.BigInteger()),
        *timestamps(),
        sa.UniqueConstraint("run_uid", name="uk_dialogue_run_uid"),
        sa.UniqueConstraint("request_id", name="uk_dialogue_run_request_id"),
    )
    op.create_table(
        "llm_invocation_ledger",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("invocation_seq", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(64)),
        sa.Column("step_no", sa.Integer()),
        sa.Column("call_kind", sa.String(32), nullable=False),
        sa.Column("streaming", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model_name", sa.String(128)),
        sa.Column("response_text", sa.Text()),
        sa.Column("tool_call_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("finish_reason", sa.String(64)),
        sa.Column("status", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_msg", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("duration_ms", sa.BigInteger()),
        *timestamps(),
    )
    op.create_table(
        "tool_invocation_ledger",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("llm_invocation_id", sa.BigInteger()),
        sa.Column("tool_call_id", sa.String(128), nullable=False),
        sa.Column("dispatch_index", sa.Integer()),
        sa.Column("agent_name", sa.String(64)),
        sa.Column("step_no", sa.Integer()),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("tool_provider", sa.String(32), nullable=False, server_default="local"),
        sa.Column("input_json", sa.JSON()),
        sa.Column("llm_observation", sa.Text()),
        sa.Column("status", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_msg", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("duration_ms", sa.BigInteger()),
        *timestamps(),
    )
    op.create_table(
        "artifact_ledger",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.BigInteger()),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("tool_invocation_id", sa.BigInteger()),
        sa.Column("tool_call_id", sa.String(128)),
        sa.Column("artifact_role", sa.String(32), nullable=False),
        sa.Column("visibility", sa.String(32), nullable=False, server_default="visible"),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_name", sa.String(128)),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(512)),
        sa.Column("download_url", sa.String(1024)),
        sa.Column("preview_url", sa.String(1024)),
        sa.Column("mime_type", sa.String(128)),
        sa.Column("file_size", sa.BigInteger()),
        sa.Column("file_hash", sa.String(128)),
        sa.Column("metadata_json", sa.JSON()),
        *timestamps(),
    )
    op.create_table(
        "visitor_identity",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("visitor_id", sa.String(128), nullable=False),
        sa.Column("token_digest", sa.String(128), nullable=False),
        sa.Column("username", sa.String(128)),
        sa.Column("last_ip", sa.String(128)),
        sa.Column("last_user_agent", sa.String(512)),
        sa.Column("last_seen_at", sa.DateTime()),
        *timestamps(),
        sa.UniqueConstraint("visitor_id", name="uk_visitor_identity_visitor_id"),
        sa.UniqueConstraint("token_digest", name="uk_visitor_identity_token_digest"),
    )
    op.create_table(
        "admin_user",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("username", sa.String(128), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
        *timestamps(),
        sa.UniqueConstraint("user_id", name="uk_admin_user_user_id"),
        sa.UniqueConstraint("username", name="uk_admin_user_username"),
    )
    op.create_table(
        "config_record",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("record_type", sa.String(64), nullable=False),
        sa.Column("record_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload", sa.JSON()),
        *timestamps(),
        sa.UniqueConstraint("record_type", "record_id", name="uk_config_record_type_id"),
    )
    op.create_table(
        "tool_output_record",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("tool_invocation_id", sa.BigInteger()),
        sa.Column("tool_call_id", sa.String(128)),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("output_json", sa.JSON()),
        *timestamps(),
    )
    op.create_table(
        "chat_model_info",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("db_type", sa.String(64)),
        sa.Column("description", sa.Text()),
        *timestamps(),
        sa.UniqueConstraint("code", name="uk_chat_model_info_code"),
    )
    op.create_table(
        "chat_model_schema",
        sa.Column("id", pk_type(), primary_key=True, autoincrement=True),
        sa.Column("model_code", sa.String(128), nullable=False),
        sa.Column("column_name", sa.String(128), nullable=False),
        sa.Column("column_type", sa.String(64)),
        sa.Column("description", sa.Text()),
        *timestamps(),
    )


def downgrade() -> None:
    for table in [
        "chat_model_schema",
        "chat_model_info",
        "tool_output_record",
        "config_record",
        "admin_user",
        "visitor_identity",
        "artifact_ledger",
        "tool_invocation_ledger",
        "llm_invocation_ledger",
        "dialogue_run_ledger",
        "dialogue_session_ledger",
    ]:
        op.drop_table(table)
