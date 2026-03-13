# Data Model Definitions - OpenClaw Monitor

## 1. 设计目标

本数据模型用于支撑 OpenClaw Monitor 的黑盒观测能力。模型分为三层：

- 原始事件存储
- 标准化实体快照
- 聚合查询结果

v1 的重点是确保“事件可追踪、状态可推导、查询可落地”。

## 2. Event

```ts
type Event = {
  eventId: string
  eventType:
    | 'agent_heartbeat'
    | 'node_heartbeat'
    | 'task_created'
    | 'task_queued'
    | 'task_started'
    | 'task_waiting'
    | 'task_progress'
    | 'task_completed'
    | 'task_failed'
    | 'model_invoked'
    | 'token_usage'
    | 'artifact_emitted'
    | 'error_logged'
    | 'alert_triggered'
    | 'alert_resolved'
  occurredAt: string
  ingestedAt: string
  traceId: string | null
  taskId: string | null
  agentId: string | null
  nodeId: string | null
  sessionId: string | null
  source: 'gateway' | 'agent' | 'node' | 'collector' | 'system'
  severity: 'info' | 'warning' | 'error' | 'critical'
  payload: Record<string, unknown>
  rawRef: string | null
}
```

## 3. Agent

```ts
type Agent = {
  id: string
  name: string
  version: string | null
  host: string | null
  connectivityStatus: 'online' | 'offline' | 'unknown'
  runtimeStatus: 'idle' | 'queued' | 'running' | 'waiting' | 'error' | 'unknown'
  currentTaskId: string | null
  lastHeartbeatAt: string | null
  lastActivityAt: string | null
  lastErrorAt: string | null
  todayTokenTotal: number
  todayTokenInput: number
  todayTokenOutput: number
  openAlertCount: number
  derivedStatusReason: string | null
}
```

## 4. Node

```ts
type Node = {
  id: string
  name: string
  host: string | null
  connectivityStatus: 'online' | 'offline' | 'unknown'
  lastHeartbeatAt: string | null
  cpuPercent: number | null
  memoryPercent: number | null
  diskPercent: number | null
  openAlertCount: number
}
```

## 5. Task

```ts
type Task = {
  id: string
  traceId: string | null
  sessionId: string | null
  taskType: string | null
  taskName: string | null
  sourceAgentId: string | null
  executorAgentId: string | null
  executorNodeId: string | null
  status: 'created' | 'queued' | 'running' | 'waiting' | 'completed' | 'failed' | 'timeout' | 'unknown'
  createdAt: string | null
  startedAt: string | null
  endedAt: string | null
  updatedAt: string | null
  durationMs: number | null
  waitReason: string | null
  attempt: number | null
  modelNames: string[]
  supplierNames: string[]
  tokenUsage: {
    input: number
    output: number
    total: number
    estimatedCost: number | null
    currency: string | null
  }
  artifactCount: number
  latestArtifactPath: string | null
  errorCode: string | null
  errorMessage: string | null
  lastEventAt: string | null
}
```

## 6. Alert

```ts
type Alert = {
  id: string
  type:
    | 'agent_offline'
    | 'node_offline'
    | 'task_timeout'
    | 'task_failed'
    | 'task_token_abnormal'
    | 'error_burst'
  severity: 'warning' | 'critical'
  status: 'open' | 'resolved' | 'suppressed'
  dedupKey: string
  title: string
  description: string | null
  relatedTaskId: string | null
  relatedAgentId: string | null
  relatedNodeId: string | null
  triggeredAt: string
  resolvedAt: string | null
  lastObservedAt: string | null
}
```

## 7. Overview

```ts
type Overview = {
  generatedAt: string
  dataLatencySeconds: number | null
  agentOnlineCount: number
  agentOfflineCount: number
  nodeOnlineCount: number
  nodeOfflineCount: number
  taskRunningCount: number
  taskWaitingCount: number
  taskFailedCount: number
  taskTimeoutCount: number
  openAlertCount: number
  todayTokenInput: number
  todayTokenOutput: number
  todayTokenTotal: number
  todayEstimatedCost: number | null
  todayErrorCount: number
}
```

## 8. Task Timeline Item

```ts
type TaskTimelineItem = {
  eventId: string
  eventType: string
  occurredAt: string
  agentId: string | null
  nodeId: string | null
  severity: 'info' | 'warning' | 'error' | 'critical'
  summary: string
  payload: Record<string, unknown>
}
```

## 9. 查询约束

- 所有列表接口必须支持分页。
- 所有趋势接口必须支持时间范围。
- 所有实体详情必须能关联到原始事件。
- 当源数据缺失时，字段允许为 `null`，但不允许伪造默认业务值。
