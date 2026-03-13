# API Endpoint Definitions - OpenClaw Monitor

## 1. 设计原则

- API 仅提供只读查询能力。
- API 面向观测场景设计，不面向任务控制。
- API 分为总览、实体列表、实体详情、事件流、告警、趋势分析六类。
- 所有列表接口必须支持分页、过滤、排序。

## 2. 通用约定

### 2.1 时间格式

- 所有时间字段使用 ISO 8601 UTC 字符串。

### 2.2 分页参数

- `page`: 页码，从 1 开始
- `page_size`: 每页数量，默认 20，最大 200

### 2.3 通用过滤参数

- `from`: 开始时间
- `to`: 结束时间
- `q`: 关键字搜索

### 2.4 列表返回格式

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

## 3. Overview

### GET /api/overview

返回系统总览数据。

Response:

```json
{
  "generatedAt": "2026-03-13T09:00:00Z",
  "dataLatencySeconds": 4,
  "agentOnlineCount": 12,
  "agentOfflineCount": 1,
  "nodeOnlineCount": 6,
  "nodeOfflineCount": 0,
  "taskRunningCount": 8,
  "taskWaitingCount": 2,
  "taskFailedCount": 1,
  "taskTimeoutCount": 0,
  "openAlertCount": 3,
  "todayTokenInput": 120000,
  "todayTokenOutput": 54000,
  "todayTokenTotal": 174000,
  "todayEstimatedCost": 18.52,
  "todayErrorCount": 7
}
```

## 4. Agents

### GET /api/agents

Params:

- `connectivity_status` (optional)
- `runtime_status` (optional)
- `has_open_alert` (optional)
- `page` / `page_size`

Response:

```json
{
  "items": [
    {
      "id": "agent-1",
      "name": "planner-agent",
      "connectivityStatus": "online",
      "runtimeStatus": "running",
      "currentTaskId": "task-123",
      "lastHeartbeatAt": "2026-03-13T08:59:55Z",
      "lastActivityAt": "2026-03-13T08:59:56Z",
      "todayTokenTotal": 32000,
      "openAlertCount": 1,
      "derivedStatusReason": "task_started without terminal event"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### GET /api/agents/{agent_id}

返回单个 Agent 详情。

### GET /api/agents/{agent_id}/events

返回某个 Agent 相关事件。

Params:

- `event_type` (optional)
- `from` / `to`
- `page` / `page_size`

## 5. Nodes

### GET /api/nodes

Params:

- `connectivity_status` (optional)
- `page` / `page_size`

### GET /api/nodes/{node_id}

返回单个 Node 详情。

### GET /api/nodes/{node_id}/events

返回某个 Node 相关事件。

## 6. Tasks

### GET /api/tasks

Params:

- `status` (optional)
- `source_agent_id` (optional)
- `executor_agent_id` (optional)
- `executor_node_id` (optional)
- `trace_id` (optional)
- `from` / `to`
- `page` / `page_size`

Response:

```json
{
  "items": [
    {
      "id": "task-123",
      "traceId": "trace-001",
      "taskType": "content_generation",
      "sourceAgentId": "agent-a",
      "executorAgentId": "agent-b",
      "executorNodeId": "node-1",
      "status": "running",
      "createdAt": "2026-03-13T08:55:00Z",
      "startedAt": "2026-03-13T08:55:10Z",
      "updatedAt": "2026-03-13T08:58:00Z",
      "durationMs": 170000,
      "tokenUsage": {
        "input": 1200,
        "output": 800,
        "total": 2000,
        "estimatedCost": 0.08,
        "currency": "USD"
      },
      "artifactCount": 1,
      "latestArtifactPath": "/artifacts/task-123/output.json",
      "errorCode": null,
      "errorMessage": null
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### GET /api/tasks/{task_id}

返回单个任务详情。

### GET /api/tasks/{task_id}/timeline

返回任务时间线，按 `occurredAt` 升序排列。

Response:

```json
[
  {
    "eventId": "evt-1",
    "eventType": "task_created",
    "occurredAt": "2026-03-13T08:55:00Z",
    "agentId": "agent-a",
    "nodeId": null,
    "severity": "info",
    "summary": "Task created",
    "payload": {}
  }
]
```

### GET /api/tasks/{task_id}/events

返回该任务相关事件的分页结果。

## 7. Events

### GET /api/events

用于统一查询事件流。

Params:

- `event_type` (optional)
- `task_id` (optional)
- `trace_id` (optional)
- `agent_id` (optional)
- `node_id` (optional)
- `severity` (optional)
- `from` / `to`
- `page` / `page_size`

Response:

```json
{
  "items": [
    {
      "eventId": "evt-001",
      "eventType": "token_usage",
      "occurredAt": "2026-03-13T08:57:00Z",
      "traceId": "trace-001",
      "taskId": "task-123",
      "agentId": "agent-b",
      "nodeId": "node-1",
      "severity": "info",
      "source": "agent",
      "payload": {
        "model_name": "gpt-4.1",
        "supplier_name": "OpenAI",
        "token_input": 1200,
        "token_output": 800,
        "total_token": 2000
      }
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

## 8. Alerts

### GET /api/alerts

Params:

- `status` (optional)
- `type` (optional)
- `severity` (optional)
- `related_task_id` (optional)
- `related_agent_id` (optional)
- `related_node_id` (optional)
- `from` / `to`
- `page` / `page_size`

### GET /api/alerts/{alert_id}

返回单条告警详情。

## 9. Metrics

### GET /api/metrics/token-trend

Params:

- `group_by`: `day | week | month`
- `dimension`: `model | supplier | agent`
- `from` / `to`

### GET /api/metrics/error-trend

Params:

- `group_by`: `hour | day`
- `from` / `to`

### GET /api/metrics/task-status-trend

Params:

- `group_by`: `hour | day`
- `from` / `to`

## 10. 返回要求

- 列表接口默认按最近更新时间倒序。
- 任务时间线默认按发生时间升序。
- 详情接口应尽量返回推导状态说明字段，便于前端展示状态来源。
- 当源数据不完整时，接口应返回 `null` 或 `unknown`，不得伪造业务值。
