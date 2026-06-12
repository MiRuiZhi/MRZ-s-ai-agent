from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

BigIntPk = BigInteger().with_variant(Integer, "sqlite")


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    create_time: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    update_time: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class DialogueSession(Base, TimestampMixin):
    __tablename__ = "dialogue_session_ledger"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    visitor_id: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latest_request_id: Mapped[str | None] = mapped_column(String(128))
    latest_query_text: Mapped[str | None] = mapped_column(Text)
    latest_summary_text: Mapped[str | None] = mapped_column(Text)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    finished_run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime)


class DialogueRun(Base, TimestampMixin):
    __tablename__ = "dialogue_run_ledger"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    run_uid: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    visitor_id: Mapped[str | None] = mapped_column(String(128))
    entry_agent: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    query_text: Mapped[str | None] = mapped_column(Text)
    final_summary_text: Mapped[str | None] = mapped_column(Text)
    llm_call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    artifact_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt_tokens_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_msg: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)


class LlmInvocation(Base, TimestampMixin):
    __tablename__ = "llm_invocation_ledger"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    invocation_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(64))
    step_no: Mapped[int | None] = mapped_column(Integer)
    call_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    streaming: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(128))
    response_text: Mapped[str | None] = mapped_column(Text)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    finish_reason: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_msg: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)


class ToolInvocation(Base, TimestampMixin):
    __tablename__ = "tool_invocation_ledger"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    llm_invocation_id: Mapped[int | None] = mapped_column(BigInteger)
    tool_call_id: Mapped[str] = mapped_column(String(128), nullable=False)
    dispatch_index: Mapped[int | None] = mapped_column(Integer)
    agent_name: Mapped[str | None] = mapped_column(String(64))
    step_no: Mapped[int | None] = mapped_column(Integer)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    tool_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    input_json: Mapped[dict | None] = mapped_column(JSON)
    llm_observation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_msg: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)


class ArtifactLedger(Base, TimestampMixin):
    __tablename__ = "artifact_ledger"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    run_id: Mapped[int | None] = mapped_column(BigInteger)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tool_invocation_id: Mapped[int | None] = mapped_column(BigInteger)
    tool_call_id: Mapped[str | None] = mapped_column(String(128))
    artifact_role: Mapped[str] = mapped_column(String(32), nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), default="visible", nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(128))
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(512))
    download_url: Mapped[str | None] = mapped_column(String(1024))
    preview_url: Mapped[str | None] = mapped_column(String(1024))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    file_hash: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)


class VisitorIdentity(Base, TimestampMixin):
    __tablename__ = "visitor_identity"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    visitor_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    token_digest: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(128))
    last_ip: Mapped[str | None] = mapped_column(String(128))
    last_user_agent: Mapped[str | None] = mapped_column(String(512))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_user"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ConfigRecord(Base, TimestampMixin):
    __tablename__ = "config_record"
    __table_args__ = (UniqueConstraint("record_type", "record_id", name="uk_config_record_type_id"),)

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    record_type: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON)


class ToolOutputRecord(Base, TimestampMixin):
    __tablename__ = "tool_output_record"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    tool_invocation_id: Mapped[int | None] = mapped_column(BigInteger)
    tool_call_id: Mapped[str | None] = mapped_column(String(128))
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    output_json: Mapped[dict | None] = mapped_column(JSON)


class ChatModelInfo(Base, TimestampMixin):
    __tablename__ = "chat_model_info"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    db_type: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)


class ChatModelSchema(Base, TimestampMixin):
    __tablename__ = "chat_model_schema"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    model_code: Mapped[str] = mapped_column(String(128), nullable=False)
    column_name: Mapped[str] = mapped_column(String(128), nullable=False)
    column_type: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
