from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class Overview(TypedDict):
    generatedAt: str
    dataLatencySeconds: int
    agentOnlineCount: int
    agentOfflineCount: int
    nodeOnlineCount: int
    nodeOfflineCount: int
    taskRunningCount: int
    taskWaitingCount: int
    taskFailedCount: int
    taskTimeoutCount: int
    openAlertCount: int
    todayTokenInput: int
    todayTokenOutput: int
    todayTokenTotal: int
    todayEstimatedCost: float
    todayErrorCount: int


class AgentItem(TypedDict):
    id: str
    name: str
    connectivityStatus: Literal["online", "offline", "unknown"]
    runtimeStatus: Literal["idle", "queued", "running", "waiting", "error", "unknown"]
    currentTaskId: str | None
    lastHeartbeatAt: str | None
    lastActivityAt: str | None
    todayTokenTotal: int
    openAlertCount: int
    derivedStatusReason: str


class AlertItem(TypedDict):
    id: str
    type: str
    severity: Literal["warning", "critical"]
    status: Literal["open", "resolved", "suppressed"]
    title: str
    description: str | None
    relatedTaskId: str | None
    relatedAgentId: str | None
    relatedNodeId: str | None
    triggeredAt: str
    resolvedAt: str | None


class TaskTokenUsage(TypedDict):
    input: int
    output: int
    total: int
    estimatedCost: float
    currency: str


class TaskItem(TypedDict):
    id: str
    traceId: str
    taskType: str
    sourceAgentId: str
    executorAgentId: str
    executorNodeId: str
    status: str
    createdAt: str
    startedAt: str
    updatedAt: str
    durationMs: int
    tokenUsage: TaskTokenUsage
    artifactCount: int
    latestArtifactPath: str | None
    errorCode: str | None
    errorMessage: str | None


class EventItem(TypedDict):
    id: str
    type: str
    title: str
    detail: str
    occurredAt: str
    severity: str
    relatedTaskId: str | None
    relatedAgentId: str | None
    relatedAlertId: str | None


class RawEventItem(TypedDict):
    id: str
    eventType: str
    occurredAt: str
    severity: str
    title: str
    detail: str
    taskId: str | None
    agentId: str | None
    alertId: str | None
    payload: dict[str, Any]


class IngestEvent(BaseModel):
    eventId: str = Field(min_length=1)
    eventType: str = Field(min_length=1)
    occurredAt: str = Field(min_length=1)
    severity: str = "info"
    title: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    taskId: str | None = None
    agentId: str | None = None
    alertId: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class GatewayDiscoveryCandidateUpdate(BaseModel):
    name: str
    base_url: str
    ws_url: str = ""
    origin: str = ""
    session_key: str = "agent:main:main"
    token: str = ""
    password: str = ""
    priority: int = Field(default=100, ge=0, le=10000)


class GatewayConfigUpdate(BaseModel):
    enabled: bool = True
    auto_capture: bool = True
    probe_interval_seconds: int = Field(default=15, ge=5, le=3600)
    mode: str = "local-first"
    default_port: int = Field(default=18789, ge=1, le=65535)
    discovery_ports: list[int] = Field(default_factory=lambda: [18789, 3000])
    base_url: str = ""
    ws_url: str = ""
    origin: str = ""
    session_key: str = "agent:main:main"
    token: str = ""
    password: str = ""
    language: str = "zh-CN"
    discovery_candidates: list[GatewayDiscoveryCandidateUpdate] = Field(default_factory=list)


class NodeCollectorIngestFileRequest(BaseModel):
    path: str = Field(min_length=1)
