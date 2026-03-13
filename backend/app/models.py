from __future__ import annotations

import json
from sqlite3 import Row


def serialize_overview(row: Row) -> dict:
    return {
        "generatedAt": row["generated_at"],
        "dataLatencySeconds": row["data_latency_seconds"],
        "agentOnlineCount": row["agent_online_count"],
        "agentOfflineCount": row["agent_offline_count"],
        "nodeOnlineCount": row["node_online_count"],
        "nodeOfflineCount": row["node_offline_count"],
        "taskRunningCount": row["task_running_count"],
        "taskWaitingCount": row["task_waiting_count"],
        "taskFailedCount": row["task_failed_count"],
        "taskTimeoutCount": row["task_timeout_count"],
        "openAlertCount": row["open_alert_count"],
        "todayTokenInput": row["today_token_input"],
        "todayTokenOutput": row["today_token_output"],
        "todayTokenTotal": row["today_token_total"],
        "todayEstimatedCost": row["today_estimated_cost"],
        "todayErrorCount": row["today_error_count"],
    }


def serialize_agent(row: Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "connectivityStatus": row["connectivity_status"],
        "runtimeStatus": row["runtime_status"],
        "currentTaskId": row["current_task_id"],
        "lastHeartbeatAt": row["last_heartbeat_at"],
        "lastActivityAt": row["last_activity_at"],
        "todayTokenTotal": row["today_token_total"],
        "openAlertCount": row["open_alert_count"],
        "derivedStatusReason": row["derived_status_reason"],
    }


def serialize_task(row: Row) -> dict:
    return {
        "id": row["id"],
        "traceId": row["trace_id"],
        "taskType": row["task_type"],
        "sourceAgentId": row["source_agent_id"],
        "executorAgentId": row["executor_agent_id"],
        "executorNodeId": row["executor_node_id"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "startedAt": row["started_at"],
        "updatedAt": row["updated_at"],
        "durationMs": row["duration_ms"],
        "tokenUsage": {
            "input": row["token_input"],
            "output": row["token_output"],
            "total": row["token_total"],
            "estimatedCost": row["estimated_cost"],
            "currency": row["currency"],
        },
        "artifactCount": row["artifact_count"],
        "latestArtifactPath": row["latest_artifact_path"],
        "errorCode": row["error_code"],
        "errorMessage": row["error_message"],
    }


def serialize_alert(row: Row) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "severity": row["severity"],
        "status": row["status"],
        "title": row["title"],
        "description": row["description"],
        "relatedTaskId": row["related_task_id"],
        "relatedAgentId": row["related_agent_id"],
        "relatedNodeId": row["related_node_id"],
        "triggeredAt": row["triggered_at"],
        "resolvedAt": row["resolved_at"],
    }


def serialize_event(row: Row) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "detail": row["detail"],
        "occurredAt": row["occurred_at"],
        "severity": row["severity"],
        "relatedTaskId": row["related_task_id"],
        "relatedAgentId": row["related_agent_id"],
        "relatedAlertId": row["related_alert_id"],
    }


def serialize_raw_event(row: Row) -> dict:
    return {
        "id": row["id"],
        "eventType": row["event_type"],
        "occurredAt": row["occurred_at"],
        "severity": row["severity"],
        "title": row["title"],
        "detail": row["detail"],
        "taskId": row["task_id"],
        "agentId": row["agent_id"],
        "alertId": row["alert_id"],
        "payload": json.loads(row["payload_json"]),
    }
