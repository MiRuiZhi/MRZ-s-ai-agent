from __future__ import annotations

import hashlib
import uuid

from agent_api.storage.models import AdminUser, ConfigRecord
from agent_api.storage.session import SessionLocal, create_all


def main() -> None:
    create_all()
    db = SessionLocal()
    try:
        if not db.query(AdminUser).filter_by(username="admin").first():
            db.add(
                AdminUser(
                    user_id=f"admin-{uuid.uuid4().hex[:8]}",
                    username="admin",
                    password_hash=hashlib.sha256("admin123".encode("utf-8")).hexdigest(),
                    status=1,
                )
            )
        defaults = [
            ("ai_agent", "react", "ReAct Agent", {"agentType": 1}),
            ("ai_agent", "plan_solve", "PlanSolve Agent", {"agentType": 2}),
            ("ai_client_model", "default-chat", "Default OpenAI Compatible Chat Model", {"usage": "chat"}),
            ("ai_client_tool_mcp", "default-mcp", "Default MCP Registry Placeholder", {"enabled": False}),
        ]
        for record_type, record_id, name, payload in defaults:
            exists = db.query(ConfigRecord).filter_by(record_type=record_type, record_id=record_id).first()
            if not exists:
                db.add(ConfigRecord(record_type=record_type, record_id=record_id, name=name, payload=payload))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
