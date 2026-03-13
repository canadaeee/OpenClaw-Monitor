from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "monitor.db"
RAW_EVENTS_PATH = DATA_DIR / "raw-events.jsonl"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS overview (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                generated_at TEXT NOT NULL,
                data_latency_seconds INTEGER NOT NULL,
                agent_online_count INTEGER NOT NULL,
                agent_offline_count INTEGER NOT NULL,
                node_online_count INTEGER NOT NULL,
                node_offline_count INTEGER NOT NULL,
                task_running_count INTEGER NOT NULL,
                task_waiting_count INTEGER NOT NULL,
                task_failed_count INTEGER NOT NULL,
                task_timeout_count INTEGER NOT NULL,
                open_alert_count INTEGER NOT NULL,
                today_token_input INTEGER NOT NULL,
                today_token_output INTEGER NOT NULL,
                today_token_total INTEGER NOT NULL,
                today_estimated_cost REAL NOT NULL,
                today_error_count INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                connectivity_status TEXT NOT NULL,
                runtime_status TEXT NOT NULL,
                current_task_id TEXT,
                last_heartbeat_at TEXT,
                last_activity_at TEXT,
                today_token_total INTEGER NOT NULL,
                open_alert_count INTEGER NOT NULL,
                derived_status_reason TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                source_agent_id TEXT NOT NULL,
                executor_agent_id TEXT NOT NULL,
                executor_node_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                token_input INTEGER NOT NULL,
                token_output INTEGER NOT NULL,
                token_total INTEGER NOT NULL,
                estimated_cost REAL NOT NULL,
                currency TEXT NOT NULL,
                artifact_count INTEGER NOT NULL,
                latest_artifact_path TEXT,
                error_code TEXT,
                error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                related_task_id TEXT,
                related_agent_id TEXT,
                related_node_id TEXT,
                triggered_at TEXT NOT NULL,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                detail TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                severity TEXT NOT NULL,
                related_task_id TEXT,
                related_agent_id TEXT,
                related_alert_id TEXT
            );

            CREATE TABLE IF NOT EXISTS raw_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                detail TEXT NOT NULL,
                task_id TEXT,
                agent_id TEXT,
                alert_id TEXT,
                payload_json TEXT NOT NULL
            );
            """
        )

        overview_count = connection.execute("SELECT COUNT(*) FROM overview").fetchone()[0]
        if overview_count:
            return

        connection.execute(
            """
            INSERT INTO overview (
                id, generated_at, data_latency_seconds, agent_online_count, agent_offline_count,
                node_online_count, node_offline_count, task_running_count, task_waiting_count,
                task_failed_count, task_timeout_count, open_alert_count, today_token_input,
                today_token_output, today_token_total, today_estimated_cost, today_error_count
            ) VALUES (
                1, '2026-03-13T09:20:00Z', 3, 6, 1, 3, 0, 4, 1, 1, 0, 2, 182000,
                94000, 276000, 21.63, 5
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO agents (
                id, name, connectivity_status, runtime_status, current_task_id,
                last_heartbeat_at, last_activity_at, today_token_total, open_alert_count,
                derived_status_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "agent-planner",
                    "planner-agent",
                    "online",
                    "running",
                    "task-240313-001",
                    "2026-03-13T09:20:00Z",
                    "2026-03-13T09:20:00Z",
                    58200,
                    0,
                    "task_started without terminal event",
                ),
                (
                    "agent-reviewer",
                    "reviewer-agent",
                    "offline",
                    "unknown",
                    None,
                    "2026-03-13T09:12:00Z",
                    "2026-03-13T09:10:41Z",
                    12400,
                    1,
                    "heartbeat missing for 30s",
                ),
            ],
        )

        connection.executemany(
            """
            INSERT INTO tasks (
                id, trace_id, task_type, source_agent_id, executor_agent_id, executor_node_id,
                status, created_at, started_at, updated_at, duration_ms, token_input, token_output,
                token_total, estimated_cost, currency, artifact_count, latest_artifact_path,
                error_code, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "task-240313-001",
                    "trace-240313-001",
                    "code_review",
                    "agent-router",
                    "agent-planner",
                    "ubuntu-gateway-01",
                    "running",
                    "2026-03-13T09:18:00Z",
                    "2026-03-13T09:18:03Z",
                    "2026-03-13T09:20:00Z",
                    145000,
                    1800,
                    1200,
                    3000,
                    0.19,
                    "USD",
                    0,
                    None,
                    None,
                    None,
                )
            ],
        )

        connection.executemany(
            """
            INSERT INTO alerts (
                id, type, severity, status, title, description, related_task_id,
                related_agent_id, related_node_id, triggered_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "alert-agent-reviewer-offline",
                    "agent_offline",
                    "warning",
                    "open",
                    "reviewer-agent offline",
                    "No heartbeat received within the offline threshold.",
                    None,
                    "agent-reviewer",
                    None,
                    "2026-03-13T09:12:30Z",
                    None,
                )
            ],
        )

        connection.executemany(
            """
            INSERT INTO events (
                id, type, title, detail, occurred_at, severity, related_task_id,
                related_agent_id, related_alert_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "evt-task-started-001",
                    "task_started",
                    "task-240313-001 开始执行",
                    "agent-planner 正在 ubuntu-gateway-01 上执行 code_review 任务。",
                    "2026-03-13T09:18:03Z",
                    "info",
                    "task-240313-001",
                    "agent-planner",
                    None,
                ),
                (
                    "evt-agent-heartbeat-001",
                    "agent_heartbeat",
                    "planner-agent 心跳上报",
                    "Agent 保持在线并持续上报运行状态。",
                    "2026-03-13T09:20:00Z",
                    "info",
                    None,
                    "agent-planner",
                    None,
                ),
                (
                    "evt-alert-triggered-001",
                    "alert_triggered",
                    "reviewer-agent offline",
                    "No heartbeat received within the offline threshold.",
                    "2026-03-13T09:12:30Z",
                    "warning",
                    None,
                    "agent-reviewer",
                    "alert-agent-reviewer-offline",
                ),
            ],
        )
