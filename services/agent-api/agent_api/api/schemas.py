from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ResponseEnvelope(BaseModel):
    code: str = "0000"
    info: str = "success"
    data: Any = None


class FileInformation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_name: Optional[str] = Field(default=None, alias="fileName")
    file_desc: Optional[str] = Field(default=None, alias="fileDesc")
    oss_url: Optional[str] = Field(default=None, alias="ossUrl")
    domain_url: Optional[str] = Field(default=None, alias="domainUrl")
    file_size: Optional[int] = Field(default=0, alias="fileSize")
    origin_file_name: Optional[str] = Field(default=None, alias="originFileName")
    origin_oss_url: Optional[str] = Field(default=None, alias="originOssUrl")
    origin_domain_url: Optional[str] = Field(default=None, alias="originDomainUrl")


class AgentMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Optional[str] = None
    content: Optional[str] = None
    message_type: Optional[str] = Field(default=None, alias="messageType")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, alias="toolCalls")
    tool_call_id: Optional[str] = Field(default=None, alias="toolCallId")
    artifact_refs: List[Dict[str, Any]] = Field(default_factory=list, alias="artifactRefs")
    reference_only: Optional[bool] = Field(default=None, alias="referenceOnly")
    command_code: Optional[str] = Field(default=None, alias="commandCode")
    upload_file: List[FileInformation] = Field(default_factory=list, alias="uploadFile")
    files: List[FileInformation] = Field(default_factory=list)


class AgentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: str = Field(alias="requestId")
    session_id: str = Field(alias="sessionId")
    visitor_id: Optional[str] = Field(default=None, alias="visitorId")
    erp: Optional[str] = None
    query: str
    agent_type: Optional[int] = Field(default=None, alias="agentType")
    base_prompt: Optional[str] = Field(default="", alias="basePrompt")
    sop_prompt: Optional[str] = Field(default="", alias="sopPrompt")
    history_dialogue: Optional[str] = Field(default="", alias="historyDialogue")
    is_stream: bool = Field(default=True, alias="isStream")
    messages: List[AgentMessage] = Field(default_factory=list)
    session_files: List[FileInformation] = Field(default_factory=list, alias="sessionFiles")
    output_style: Optional[str] = Field(default=None, alias="outputStyle")
    ai_agent_id: Optional[str] = Field(default=None, alias="aiAgentId")


class GptQueryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str
    session_id: str = Field(alias="sessionId")
    request_id: Optional[str] = Field(default=None, alias="requestId")
    deep_think: int = Field(default=0, alias="deepThink")
    output_style: Optional[str] = Field(default=None, alias="outputStyle")
    trace_id: Optional[str] = Field(default=None, alias="traceId")
    user: Optional[str] = None
    ai_agent_id: Optional[str] = Field(default=None, alias="aiAgentId")
    session_files: List[FileInformation] = Field(default_factory=list, alias="sessionFiles")


class VisitorNamingRequest(BaseModel):
    visitor_name: str = Field(validation_alias=AliasChoices("visitorName", "username"))
    visitor_id: Optional[str] = Field(default=None, alias="visitorId")


class WorkspaceImageGenerationRequest(BaseModel):
    prompt: str
    mode: Optional[str] = None
    file_names: List[str] = Field(default_factory=list, alias="fileNames")
    request_id: Optional[str] = Field(default=None, alias="requestId")
