from __future__ import annotations

import json
import uuid
from functools import lru_cache
from types import SimpleNamespace
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select

from agent_api.api.schemas import (
    AgentRequest,
    GptQueryRequest,
    ResponseEnvelope,
    VisitorNamingRequest,
    WorkspaceImageGenerationRequest,
)
from agent_api.runtime import AgentRuntime
from agent_api.settings import Settings, get_settings
from agent_api.storage.models import ConfigRecord


@lru_cache(maxsize=1)
def _runtime_singleton() -> AgentRuntime:
    return AgentRuntime(get_settings())


def get_runtime() -> AgentRuntime:
    return _runtime_singleton()


router = APIRouter()


@router.get("/web/health")
async def health() -> str:
    return "ok"


async def _sse_stream(runtime: AgentRuntime, request: AgentRequest):
    async for event in runtime.stream_agent(request):
        yield f"data: {event.to_sse_data()}\n\n"


@router.post("/AutoAgent")
async def auto_agent(request: AgentRequest, runtime: AgentRuntime = Depends(get_runtime)):
    return StreamingResponse(_sse_stream(runtime, request), media_type="text/event-stream")


@router.post("/web/api/v1/gpt/queryAgentStreamIncr")
async def query_agent_stream(request: GptQueryRequest, runtime: AgentRuntime = Depends(get_runtime)):
    return StreamingResponse(
        _sse_stream(runtime, runtime.convert_gpt_query(request)),
        media_type="text/event-stream",
    )


@router.get("/api/agent/visitor/bootstrap")
async def visitor_bootstrap():
    visitor_id = f"visitor-{uuid.uuid4().hex[:16]}"
    return ResponseEnvelope(
        data={
            "visitorId": visitor_id,
            "visitorToken": visitor_id,
            "visitorName": "匿名访客",
            "username": "匿名访客",
            "named": True,
        }
    )


@router.post("/api/agent/visitor/naming")
async def visitor_naming(request: VisitorNamingRequest):
    return ResponseEnvelope(
        data={
            "visitorName": request.visitor_name,
            "username": request.visitor_name,
            "named": True,
        }
    )


@router.get("/api/agent/conversation/sessions")
async def list_sessions(limit: int = 20, runtime: AgentRuntime = Depends(get_runtime)):
    return ResponseEnvelope(data=runtime.ledger.list_session_summaries(limit=limit))


@router.get("/api/agent/conversation/sessions/{session_id}")
async def session_detail(session_id: str, runtime: AgentRuntime = Depends(get_runtime)):
    runs = runtime.ledger.get_session_runs(session_id)
    return ResponseEnvelope(
        data={
            "sessionId": session_id,
            "title": runs[-1]["queryText"][:30] if runs and runs[-1].get("queryText") else session_id,
            "status": runs[-1]["status"] if runs else "RUNNING",
            "runs": runs,
        }
    )


@router.delete("/api/agent/conversation/sessions/{session_id}")
async def delete_session(session_id: str, runtime: AgentRuntime = Depends(get_runtime)):
    deleted = runtime.ledger.delete_session(session_id)
    return ResponseEnvelope(data={"sessionId": session_id, "deleted": deleted})


@router.post("/api/agent/file/upload")
async def upload_file(
    file: UploadFile,
    session_id: str = Form(alias="sessionId"),
    settings: Settings = Depends(get_settings),
):
    from agent_api.integrations.tool_runtime import ToolRuntimeClient

    filename = file.filename or "upload"
    content = await file.read()
    client = ToolRuntimeClient(settings.tool_runtime_base_url)
    response = await client.upload_file_data(
        request_id=session_id,
        filename=filename,
        content=content,
        content_type=file.content_type,
    )
    preview_url = response.get("domainUrl") or response.get("previewUrl") or response.get("downloadUrl") or ""
    download_url = response.get("downloadUrl") or response.get("ossUrl") or preview_url
    file_size = response.get("fileSize") or len(content)
    return ResponseEnvelope(
        data={
            "name": filename,
            "url": preview_url,
            "type": file.content_type or "application/octet-stream",
            "size": file_size,
            "previewUrl": preview_url,
            "downloadUrl": download_url,
            "resourceKey": f"{session_id}/{filename}",
            "mimeType": file.content_type,
            "originFileName": filename,
        }
    )


@router.post("/api/agent/image-generation/generate")
async def image_generation(request: WorkspaceImageGenerationRequest, settings: Settings = Depends(get_settings)):
    from agent_api.integrations.tool_runtime import ToolRuntimeClient

    client = ToolRuntimeClient(settings.tool_runtime_base_url)
    response = await client.post_json(
        "/v1/tool/image_generation",
        {
            "requestId": request.request_id or str(uuid.uuid4()),
            "prompt": request.prompt,
            "mode": request.mode,
            "fileNames": request.file_names,
            "stream": False,
        },
    )
    return ResponseEnvelope(data=response)


@router.get("/api/agent/image-generation/history")
async def image_generation_history():
    return ResponseEnvelope(data={"records": [], "total": 0})


@router.get("/api/agent/role-library/list")
async def role_library():
    return ResponseEnvelope(data=[{"agentId": "react", "agentName": "ReAct", "available": True, "defaultRole": True}])


@router.get("/data/allModels")
async def all_models():
    return ResponseEnvelope(data=[])


@router.get("/data/previewData")
async def preview_data(modelCode: str):
    return ResponseEnvelope(data={"modelCode": modelCode, "rows": []})


@router.post("/data/chatQuery")
async def data_chat_query(body: Dict[str, Any], runtime: AgentRuntime = Depends(get_runtime)):
    content = body.get("content") or body.get("query") or body.get("message") or ""
    request_id = str(body.get("requestId") or uuid.uuid4())
    session_id = str(body.get("sessionId") or f"data-session-{uuid.uuid4().hex[:16]}")
    context = SimpleNamespace(
        request_id=request_id,
        session_id=session_id,
        query=content,
        visitor_id=body.get("visitorId"),
        entry_agent="data_agent",
    )
    runtime.ledger.begin_run(context, "data_agent")

    async def stream():
        final_summary = "输出结果"
        events = [
            {"eventType": "THINK", "data": f"正在分析问题：{content}"},
            {"eventType": "CHART_DATA", "data": []},
            {"eventType": "READY"},
        ]
        for event in events:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        runtime.ledger.finish_run(context, "success", final_summary)

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/data/{path:path}")
async def data_compat(path: str, body: Dict[str, Any]):
    return ResponseEnvelope(data={"path": path, "request": body, "message": "data endpoint is wired for compatibility"})


_ADMIN_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}


def _admin_record_id(resource: str, item: Dict[str, Any]) -> str:
    candidates = [
        "id",
        "recordId",
        f"{resource}Id",
        resource.replace("_", "") + "Id",
        "agentId",
        "modelCode",
        "clientId",
        "promptId",
        "mcpId",
        "userId",
    ]
    for key in candidates:
        if item.get(key):
            return str(item[key])
    return str(uuid.uuid4())


def _admin_record_name(item: Dict[str, Any], fallback: str) -> str:
    for key in ["name", "agentName", "modelName", "clientName", "promptName", "username"]:
        if item.get(key):
            return str(item[key])
    return fallback


def _admin_payload(row: ConfigRecord) -> Dict[str, Any]:
    payload = dict(row.payload or {})
    payload.setdefault("id", row.record_id)
    return payload


@router.api_route("/api/v1/admin/{resource}/{action:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def admin_compat(
    resource: str,
    action: str,
    body: Optional[Dict[str, Any]] = None,
    runtime: AgentRuntime = Depends(get_runtime),
):
    session_factory = getattr(runtime.ledger, "session_factory", None)
    if session_factory is not None:
        return _admin_compat_sql(session_factory, resource, action, body)

    store = _ADMIN_STORE.setdefault(resource, {})
    normalized_action = action.split("/")[0]
    if normalized_action == "create":
        item = dict(body or {})
        item_id = _admin_record_id(resource, item)
        item["id"] = item_id
        store[item_id] = item
        return ResponseEnvelope(data=item)
    if normalized_action.startswith("query-all") or normalized_action == "query-enabled":
        return ResponseEnvelope(data=list(store.values()))
    if normalized_action == "query-list":
        return ResponseEnvelope(data={"records": list(store.values()), "total": len(store)})
    return ResponseEnvelope(data={"resource": resource, "action": action, "storeSize": len(store)})


def _admin_compat_sql(session_factory, resource: str, action: str, body: Optional[Dict[str, Any]]):
    normalized_action = action.split("/")[0]
    with session_factory() as session:
        if normalized_action in {"create", "update"}:
            item = dict(body or {})
            item_id = _admin_record_id(resource, item)
            item.setdefault("id", item_id)
            record = session.scalar(
                select(ConfigRecord).where(
                    ConfigRecord.record_type == resource,
                    ConfigRecord.record_id == item_id,
                )
            )
            if record is None:
                record = ConfigRecord(record_type=resource, record_id=item_id)
                session.add(record)
            record.name = _admin_record_name(item, item_id)
            record.status = 0 if item.get("enabled") is False else int(item.get("status", 1) or 1)
            record.deleted = 0
            record.payload = item
            session.commit()
            return ResponseEnvelope(data=item)

        if normalized_action in {"delete", "remove"}:
            item = dict(body or {})
            item_id = action.split("/", 1)[1] if "/" in action else _admin_record_id(resource, item)
            record = session.scalar(
                select(ConfigRecord).where(
                    ConfigRecord.record_type == resource,
                    ConfigRecord.record_id == item_id,
                )
            )
            if record is not None:
                record.deleted = 1
                record.status = 0
                session.commit()
            return ResponseEnvelope(data={"id": item_id, "deleted": True})

        query = select(ConfigRecord).where(ConfigRecord.record_type == resource, ConfigRecord.deleted == 0)
        if normalized_action == "query-enabled":
            query = query.where(ConfigRecord.status == 1)
        rows = session.scalars(query.order_by(ConfigRecord.id.desc())).all()
        payloads = [_admin_payload(row) for row in rows]
        if normalized_action == "query-list":
            return ResponseEnvelope(data={"records": payloads, "total": len(payloads)})
        if normalized_action.startswith("query-all") or normalized_action == "query-enabled":
            return ResponseEnvelope(data=payloads)
        return ResponseEnvelope(data={"resource": resource, "action": action, "storeSize": len(payloads)})
