from __future__ import annotations

import json
from datetime import datetime, timezone

from .db import RAW_EVENTS_PATH, get_connection
from .models import (
    serialize_agent,
    serialize_alert,
    serialize_event,
    serialize_overview,
    serialize_raw_event,
    serialize_task,
)
from .schemas import AgentItem, AlertItem, EventItem, IngestEvent, Overview, RawEventItem, TaskItem


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _utc_from_epoch(epoch: int | float) -> str:
    seconds = epoch / 1000 if epoch > 1e12 else epoch
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_epoch_ms(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _infer_task_type_from_session_key(key: str) -> str:
    lowered = key.lower()
    if ":cron:" in lowered:
        return "cron"
    if ":discord:" in lowered:
        return "discord"
    return "session"


def get_overview() -> Overview:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM overview WHERE id = 1").fetchone()
    return serialize_overview(row)


def list_agents() -> list[AgentItem]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM agents ORDER BY name").fetchall()
    return [serialize_agent(row) for row in rows]


def get_agent(agent_id: str) -> AgentItem | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    return serialize_agent(row) if row else None


def list_tasks() -> list[TaskItem]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM tasks ORDER BY updated_at DESC").fetchall()
    return [serialize_task(row) for row in rows]


def get_task(task_id: str) -> TaskItem | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return serialize_task(row) if row else None


def list_alerts() -> list[AlertItem]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM alerts ORDER BY triggered_at DESC").fetchall()
    return [serialize_alert(row) for row in rows]


def get_alert(alert_id: str) -> AlertItem | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    return serialize_alert(row) if row else None


def list_events(
    *,
    event_type: str | None = None,
    related_task_id: str | None = None,
    related_agent_id: str | None = None,
    severity: str | None = None,
    limit: int = 200,
) -> list[EventItem]:
    query = "SELECT * FROM events"
    conditions: list[str] = []
    parameters: list[str] = []

    if event_type:
        conditions.append("type = ?")
        parameters.append(event_type)
    if related_task_id:
        conditions.append("related_task_id = ?")
        parameters.append(related_task_id)
    if related_agent_id:
        conditions.append("related_agent_id = ?")
        parameters.append(related_agent_id)
    if severity:
        conditions.append("severity = ?")
        parameters.append(severity)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY occurred_at DESC LIMIT ?"
    parameters.append(max(1, min(int(limit), 500)))

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [serialize_event(row) for row in rows]


def list_raw_events(
    *,
    event_type: str | None = None,
    task_id: str | None = None,
    agent_id: str | None = None,
    limit: int = 200,
) -> list[RawEventItem]:
    query = "SELECT * FROM raw_events"
    conditions: list[str] = []
    parameters: list[str] = []

    if event_type:
        conditions.append("event_type = ?")
        parameters.append(event_type)
    if task_id:
        conditions.append("task_id = ?")
        parameters.append(task_id)
    if agent_id:
        conditions.append("agent_id = ?")
        parameters.append(agent_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY occurred_at DESC LIMIT ?"
    parameters.append(max(1, min(int(limit), 500)))

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [serialize_raw_event(row) for row in rows]


def get_task_timeline(task_id: str) -> list[EventItem]:
    return list_events(related_task_id=task_id)


def ingest_event(event: IngestEvent) -> dict:
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT 1 FROM raw_events WHERE id = ?",
            (event.eventId,),
        ).fetchone()
        if existing:
            return {"accepted": True, "eventId": event.eventId, "duplicate": True}

        connection.execute(
            """
            INSERT OR REPLACE INTO raw_events (
                id, event_type, occurred_at, severity, title, detail,
                task_id, agent_id, alert_id, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.eventId,
                event.eventType,
                event.occurredAt,
                event.severity,
                event.title,
                event.detail,
                event.taskId,
                event.agentId,
                event.alertId,
                json.dumps(event.payload, ensure_ascii=False),
            ),
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO events (
                id, type, title, detail, occurred_at, severity,
                related_task_id, related_agent_id, related_alert_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.eventId,
                event.eventType,
                event.title,
                event.detail,
                event.occurredAt,
                event.severity,
                event.taskId,
                event.agentId,
                event.alertId,
            ),
        )
        _apply_event(connection, event)
        _refresh_overview(connection)

    _append_raw_event(event)
    return {"accepted": True, "eventId": event.eventId}


def _append_raw_event(event: IngestEvent) -> None:
    RAW_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_EVENTS_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")


def _apply_event(connection, event: IngestEvent) -> None:
    payload = _event_payload(event)

    if event.eventType == "token_snapshot" and event.taskId:
        token_input = _int_payload(payload, "tokenInput", "input", default=0)
        token_output = _int_payload(payload, "tokenOutput", "output", default=0)
        token_total = _int_payload(payload, "totalToken", "total", default=token_input + token_output)
        estimated_cost = _float_payload(payload, "estimatedCost", default=0.0)
        currency = _payload_first(payload, "currency", default="USD")
        duration_ms = _int_payload(payload, "durationMs", default=0)
        created_at = _payload_first(payload, "startedAt", default=event.occurredAt)
        updated_at = _payload_first(payload, "endedAt", default=event.occurredAt)
        task_type = _payload_first(payload, "taskType", "chatType", default=_infer_task_type_from_session_key(event.taskId))
        trace_id = _payload_first(payload, "traceId", default=event.taskId)
        executor_agent_id = _payload_first(payload, "agentId", default=event.agentId or "unknown")

        previous = connection.execute(
            "SELECT token_total FROM tasks WHERE id = ?",
            (event.taskId,),
        ).fetchone()
        previous_total = int(previous[0]) if previous else 0
        delta_total = max(0, token_total - previous_total)

        connection.execute(
            """
            INSERT INTO tasks (
                id, trace_id, task_type, source_agent_id, executor_agent_id, executor_node_id,
                status, created_at, started_at, updated_at, duration_ms, token_input, token_output,
                token_total, estimated_cost, currency, artifact_count, latest_artifact_path,
                error_code, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?, ?, 0, ?, ?, ?, ?, ?, 0, NULL, NULL, NULL)
            ON CONFLICT(id) DO UPDATE SET
                task_type = excluded.task_type,
                executor_agent_id = excluded.executor_agent_id,
                created_at = CASE WHEN tasks.created_at > excluded.created_at THEN excluded.created_at ELSE tasks.created_at END,
                started_at = CASE WHEN tasks.started_at > excluded.started_at THEN excluded.started_at ELSE tasks.started_at END,
                updated_at = excluded.updated_at,
                token_input = excluded.token_input,
                token_output = excluded.token_output,
                token_total = excluded.token_total,
                estimated_cost = excluded.estimated_cost,
                currency = excluded.currency
            """,
            (
                event.taskId,
                trace_id,
                task_type,
                executor_agent_id,
                executor_agent_id,
                "node",
                created_at,
                created_at,
                updated_at,
                token_input,
                token_output,
                token_total,
                estimated_cost,
                currency,
            ),
        )
        if duration_ms > 0:
            connection.execute(
                "UPDATE tasks SET duration_ms = ? WHERE id = ?",
                (duration_ms, event.taskId),
            )

        if event.agentId:
            # Best-effort daily aggregation: increment by observed delta.
            connection.execute(
                """
                INSERT INTO agents (
                    id, name, connectivity_status, runtime_status, current_task_id,
                    last_heartbeat_at, last_activity_at, today_token_total, open_alert_count,
                    derived_status_reason
                ) VALUES (?, ?, 'online', 'idle', NULL, ?, ?, ?, 0, ?)
                ON CONFLICT(id) DO UPDATE SET
                    connectivity_status = 'online',
                    last_activity_at = excluded.last_activity_at,
                    today_token_total = today_token_total + ?,
                    derived_status_reason = excluded.derived_status_reason
                """,
                (
                    event.agentId,
                    event.agentId,
                    event.occurredAt,
                    event.occurredAt,
                    delta_total,
                    "token snapshot update",
                    delta_total,
                ),
            )
        return

    if event.eventType == "health":
        ok = bool(payload.get("ok", True))
        gateway_ts = _parse_epoch_ms(payload.get("ts"))
        observed_at = _utc_from_epoch(gateway_ts) if gateway_ts is not None else event.occurredAt
        derived_status_reason = "gateway health snapshot"

        agents = payload.get("agents")
        if isinstance(agents, list):
            for item in agents:
                if not isinstance(item, dict):
                    continue
                agent_id = item.get("agentId")
                if not isinstance(agent_id, str) or not agent_id.strip():
                    continue
                agent_id = agent_id.strip()
                name = item.get("name")
                agent_name = name.strip() if isinstance(name, str) and name.strip() else agent_id
                sessions = item.get("sessions") if isinstance(item.get("sessions"), dict) else {}
                recent = sessions.get("recent") if isinstance(sessions.get("recent"), list) else []
                most_recent_ms = None
                for entry in recent:
                    if not isinstance(entry, dict):
                        continue
                    updated_at_ms = _parse_epoch_ms(entry.get("updatedAt"))
                    if updated_at_ms is None:
                        continue
                    most_recent_ms = updated_at_ms if most_recent_ms is None else max(most_recent_ms, updated_at_ms)
                last_activity_at = _utc_from_epoch(most_recent_ms) if most_recent_ms is not None else observed_at

                connection.execute(
                    """
                    INSERT INTO agents (
                        id, name, connectivity_status, runtime_status, current_task_id,
                        last_heartbeat_at, last_activity_at, today_token_total, open_alert_count,
                        derived_status_reason
                    ) VALUES (?, ?, ?, 'idle', NULL, ?, ?, 0, 0, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        connectivity_status = excluded.connectivity_status,
                        last_heartbeat_at = excluded.last_heartbeat_at,
                        last_activity_at = excluded.last_activity_at,
                        derived_status_reason = excluded.derived_status_reason
                    """,
                    (
                        agent_id,
                        agent_name,
                        "online" if ok else "offline",
                        observed_at,
                        last_activity_at,
                        derived_status_reason,
                    ),
                )

                for entry in recent[:50]:
                    if not isinstance(entry, dict):
                        continue
                    key = entry.get("key")
                    if not isinstance(key, str) or not key.strip():
                        continue
                    updated_at_ms = _parse_epoch_ms(entry.get("updatedAt"))
                    updated_at = _utc_from_epoch(updated_at_ms) if updated_at_ms is not None else last_activity_at
                    task_type = _infer_task_type_from_session_key(key)
                    connection.execute(
                        """
                        INSERT INTO tasks (
                            id, trace_id, task_type, source_agent_id, executor_agent_id, executor_node_id,
                            status, created_at, started_at, updated_at, duration_ms, token_input, token_output,
                            token_total, estimated_cost, currency, artifact_count, latest_artifact_path,
                            error_code, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?, ?, 0, 0, 0, 0, 0, 'USD', 0, NULL, NULL, NULL)
                        ON CONFLICT(id) DO UPDATE SET
                            status = 'running',
                            updated_at = excluded.updated_at,
                            executor_agent_id = excluded.executor_agent_id,
                            executor_node_id = excluded.executor_node_id
                        """,
                        (
                            key,
                            key,
                            task_type,
                            agent_id,
                            agent_id,
                            "gateway",
                            updated_at,
                            updated_at,
                            updated_at,
                        ),
                    )
        return

    if event.eventType == "agent_heartbeat" and event.agentId:
        connection.execute(
            """
            INSERT INTO agents (
                id, name, connectivity_status, runtime_status, current_task_id,
                last_heartbeat_at, last_activity_at, today_token_total, open_alert_count,
                derived_status_reason
            ) VALUES (?, ?, 'online', 'idle', NULL, ?, ?, 0, 0, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                connectivity_status = 'online',
                last_heartbeat_at = excluded.last_heartbeat_at,
                last_activity_at = excluded.last_activity_at,
                derived_status_reason = excluded.derived_status_reason
            """,
            (
                event.agentId,
                payload.get("agentName", event.agentId),
                event.occurredAt,
                event.occurredAt,
                event.detail,
            ),
        )
        return

    if event.eventType == "node_heartbeat" and event.agentId:
        connection.execute(
            """
            INSERT INTO agents (
                id, name, connectivity_status, runtime_status, current_task_id,
                last_heartbeat_at, last_activity_at, today_token_total, open_alert_count,
                derived_status_reason
            ) VALUES (?, ?, 'online', 'idle', NULL, ?, ?, 0, 0, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                connectivity_status = 'online',
                last_heartbeat_at = excluded.last_heartbeat_at,
                last_activity_at = excluded.last_activity_at,
                derived_status_reason = excluded.derived_status_reason
            """,
            (
                event.agentId,
                payload.get("agentName", event.agentId),
                event.occurredAt,
                event.occurredAt,
                event.detail,
            ),
        )
        return

    if event.eventType == "task_started" and event.taskId:
        executor_node_id = _payload_first(payload, "executorNodeId", "nodeId", default="unknown-node")
        executor_agent_id = _payload_first(payload, "executorAgentId", "agentId", default=event.agentId or "unknown")
        source_agent_id = _payload_first(payload, "sourceAgentId", default=event.agentId or "unknown")
        task_type = _payload_first(payload, "taskType", default="unknown")
        trace_id = _payload_first(payload, "traceId", default=event.taskId)
        created_at = _payload_first(payload, "createdAt", default=event.occurredAt)
        connection.execute(
            """
            INSERT INTO tasks (
                id, trace_id, task_type, source_agent_id, executor_agent_id, executor_node_id,
                status, created_at, started_at, updated_at, duration_ms, token_input, token_output,
                token_total, estimated_cost, currency, artifact_count, latest_artifact_path,
                error_code, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?, ?, 0, 0, 0, 0, 0, 'USD', 0, NULL, NULL, NULL)
            ON CONFLICT(id) DO UPDATE SET
                status = 'running',
                executor_agent_id = excluded.executor_agent_id,
                executor_node_id = excluded.executor_node_id,
                updated_at = excluded.updated_at
            """,
            (
                event.taskId,
                trace_id,
                task_type,
                source_agent_id,
                executor_agent_id,
                executor_node_id,
                created_at,
                event.occurredAt,
                event.occurredAt,
            ),
        )
        if event.agentId:
            connection.execute(
                """
                UPDATE agents
                SET runtime_status = 'running', current_task_id = ?, last_activity_at = ?, connectivity_status = 'online',
                    derived_status_reason = ?
                WHERE id = ?
                """,
                (event.taskId, event.occurredAt, event.detail, event.agentId),
            )
        return

    if event.eventType == "task_completed" and event.taskId:
        duration_ms = _int_payload(payload, "durationMs", default=0)
        artifact_path = _payload_first(payload, "artifactPath", "latestArtifactPath")
        completed_status = _payload_first(payload, "status", default="completed")
        connection.execute(
            """
            UPDATE tasks
            SET status = ?, updated_at = ?, duration_ms = CASE WHEN ? > 0 THEN ? ELSE duration_ms END,
                latest_artifact_path = COALESCE(?, latest_artifact_path)
            WHERE id = ?
            """,
            (
                completed_status,
                event.occurredAt,
                duration_ms,
                duration_ms,
                artifact_path,
                event.taskId,
            ),
        )
        if event.agentId:
            connection.execute(
                """
                UPDATE agents
                SET runtime_status = 'idle', current_task_id = NULL, last_activity_at = ?, derived_status_reason = ?
                WHERE id = ?
                """,
                (event.occurredAt, event.detail, event.agentId),
            )
        return

    if event.eventType == "task_waiting" and event.taskId:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'waiting', updated_at = ?
            WHERE id = ?
            """,
            (event.occurredAt, event.taskId),
        )
        if event.agentId:
            connection.execute(
                """
                UPDATE agents
                SET runtime_status = 'waiting', current_task_id = ?, last_activity_at = ?, derived_status_reason = ?
                WHERE id = ?
                """,
                (event.taskId, event.occurredAt, event.detail, event.agentId),
            )
        return

    if event.eventType == "task_failed" and event.taskId:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'failed', updated_at = ?, error_code = ?, error_message = ?, duration_ms = CASE WHEN ? > 0 THEN ? ELSE duration_ms END
            WHERE id = ?
            """,
            (
                event.occurredAt,
                _payload_first(payload, "errorCode"),
                _payload_first(payload, "errorMessage", default=event.detail),
                _int_payload(payload, "durationMs", default=0),
                _int_payload(payload, "durationMs", default=0),
                event.taskId,
            ),
        )
        if event.agentId:
            connection.execute(
                """
                UPDATE agents
                SET runtime_status = 'error', current_task_id = ?, last_activity_at = ?, derived_status_reason = ?, open_alert_count = open_alert_count + 1
                WHERE id = ?
                """,
                (event.taskId, event.occurredAt, event.detail, event.agentId),
            )
        return

    if event.eventType == "token_usage" and event.taskId:
        token_input = _int_payload(payload, "tokenInput", "input", default=0)
        token_output = _int_payload(payload, "tokenOutput", "output", default=0)
        token_total = _int_payload(payload, "totalToken", "total", default=token_input + token_output)
        estimated_cost = _float_payload(payload, "estimatedCost", default=0.0)
        currency = _payload_first(payload, "currency", default="USD")
        connection.execute(
            """
            UPDATE tasks
            SET token_input = token_input + ?, token_output = token_output + ?, token_total = token_total + ?,
                estimated_cost = estimated_cost + ?, currency = ?, updated_at = ?
            WHERE id = ?
            """,
            (token_input, token_output, token_total, estimated_cost, currency, event.occurredAt, event.taskId),
        )
        if event.agentId:
            connection.execute(
                """
                UPDATE agents
                SET today_token_total = today_token_total + ?, last_activity_at = ?, connectivity_status = 'online'
                WHERE id = ?
                """,
                (token_total, event.occurredAt, event.agentId),
            )
        return

    if event.eventType == "alert_triggered" and event.alertId:
        connection.execute(
            """
            INSERT INTO alerts (
                id, type, severity, status, title, description, related_task_id,
                related_agent_id, related_node_id, triggered_at, resolved_at
            ) VALUES (?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(id) DO UPDATE SET
                severity = excluded.severity,
                status = 'open',
                title = excluded.title,
                description = excluded.description,
                related_task_id = excluded.related_task_id,
                related_agent_id = excluded.related_agent_id,
                related_node_id = excluded.related_node_id,
                triggered_at = excluded.triggered_at,
                resolved_at = NULL
            """,
            (
                event.alertId,
                event.payload.get("alertType", "generic"),
                # alert fields may live in either wrapper or nested payload
                event.severity,
                event.title,
                event.detail,
                event.taskId,
                event.agentId,
                _payload_first(payload, "nodeId"),
                event.occurredAt,
            ),
        )
        return

    if event.eventType == "alert_resolved" and event.alertId:
        connection.execute(
            "UPDATE alerts SET status = 'resolved', resolved_at = ? WHERE id = ?",
            (event.occurredAt, event.alertId),
        )


def _payload_first(payload: dict, *keys: str, default=None):
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return default


def _int_payload(payload: dict, *keys: str, default: int = 0) -> int:
    value = _payload_first(payload, *keys, default=default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _event_payload(event: IngestEvent) -> dict:
    payload = event.payload or {}
    nested = payload.get("payload")
    if isinstance(nested, dict):
        return nested
    return payload


def _float_payload(payload: dict, *keys: str, default: float = 0.0) -> float:
    value = _payload_first(payload, *keys, default=default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _refresh_overview(connection) -> None:
    agent_online_count = connection.execute(
        "SELECT COUNT(*) FROM agents WHERE connectivity_status = 'online'"
    ).fetchone()[0]
    agent_offline_count = connection.execute(
        "SELECT COUNT(*) FROM agents WHERE connectivity_status = 'offline'"
    ).fetchone()[0]
    task_running_count = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'running'"
    ).fetchone()[0]
    task_waiting_count = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'waiting'"
    ).fetchone()[0]
    task_failed_count = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'failed'"
    ).fetchone()[0]
    open_alert_count = connection.execute(
        "SELECT COUNT(*) FROM alerts WHERE status = 'open'"
    ).fetchone()[0]
    today_error_count = connection.execute(
        "SELECT COUNT(*) FROM events WHERE severity IN ('error', 'critical', 'warning')"
    ).fetchone()[0]
    token_row = connection.execute(
        "SELECT COALESCE(SUM(token_input), 0), COALESCE(SUM(token_output), 0), COALESCE(SUM(token_total), 0), COALESCE(SUM(estimated_cost), 0) FROM tasks"
    ).fetchone()

    connection.execute(
        """
        UPDATE overview
        SET generated_at = ?, data_latency_seconds = ?, agent_online_count = ?, agent_offline_count = ?,
            node_online_count = 0, node_offline_count = 0,
            task_running_count = ?, task_waiting_count = ?, task_failed_count = ?, task_timeout_count = 0,
            open_alert_count = ?, today_error_count = ?, today_token_input = ?, today_token_output = ?, today_token_total = ?,
            today_estimated_cost = ?
        WHERE id = 1
        """,
        (
            utc_now(),
            1,
            agent_online_count,
            agent_offline_count,
            task_running_count,
            task_waiting_count,
            task_failed_count,
            open_alert_count,
            today_error_count,
            token_row[0],
            token_row[1],
            token_row[2],
            token_row[3],
        ),
    )
