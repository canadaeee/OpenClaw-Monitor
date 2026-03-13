from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .collector import OpenClawCollector


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class NodeCollectorConfig:
    enabled: bool = True
    mode: str = "local-node"
    source_type: str = "jsonl"
    source_path: str = ""
    poll_interval_seconds: int = 5


@dataclass
class NodeCollectorState:
    enabled: bool = True
    mode: str = "local-node"
    source_type: str = "jsonl"
    source_path: str = ""
    lastReadAt: str | None = None
    lastIngestAt: str | None = None
    lastError: str | None = None
    ingestedCount: int = 0
    note: str = "Node-side collector skeleton is ready."
    sampleEventTypes: list[str] = field(default_factory=lambda: [
        "agent_heartbeat",
        "node_heartbeat",
        "task_started",
        "task_waiting",
        "task_completed",
        "task_failed",
        "token_usage",
        "artifact_emitted",
        "error_event",
    ])


class NodeSideCollector:
    def __init__(self, gateway_collector: OpenClawCollector, config: NodeCollectorConfig | None = None):
        self.gateway_collector = gateway_collector
        self.config = config or NodeCollectorConfig()
        self.state = NodeCollectorState(
            enabled=self.config.enabled,
            mode=self.config.mode,
            source_type=self.config.source_type,
            source_path=self.config.source_path,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "enabled": self.state.enabled,
            "mode": self.state.mode,
            "sourceType": self.state.source_type,
            "sourcePath": self.state.source_path,
            "lastReadAt": self.state.lastReadAt,
            "lastIngestAt": self.state.lastIngestAt,
            "lastError": self.state.lastError,
            "ingestedCount": self.state.ingestedCount,
            "note": self.state.note,
            "sampleEventTypes": self.state.sampleEventTypes,
            "recommendedPath": str((Path(__file__).resolve().parents[2] / "data" / "node-events.jsonl")),
        }

    def ingest_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.state.lastReadAt = utc_now()
        result = self.gateway_collector.ingest_gateway_event(payload)
        self.state.lastIngestAt = utc_now()
        self.state.ingestedCount += 1
        self.state.lastError = None
        return result

    def ingest_lines(self, lines: Iterable[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for line in lines:
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                self.state.lastError = f"invalid json line: {exc}"
                continue
            if not isinstance(payload, dict):
                self.state.lastError = "json line is not an object"
                continue
            results.append(self.ingest_payload(payload))
        return results

    def ingest_jsonl_file(self, path: str | Path) -> list[dict[str, Any]]:
        file_path = Path(path)
        self.state.source_path = str(file_path)
        if not file_path.exists():
            self.state.lastError = f"source not found: {file_path}"
            return []

        with file_path.open("r", encoding="utf-8") as handle:
            return self.ingest_lines(handle)

    def sample_jsonl(self) -> str:
        sample_events = [
            {
                "eventId": "node-heartbeat-001",
                "eventType": "node_heartbeat",
                "occurredAt": utc_now(),
                "severity": "info",
                "title": "Node heartbeat",
                "detail": "OpenClaw node heartbeat received",
                "agentId": "agent-main",
                "payload": {
                    "nodeId": "node-local",
                    "status": "online",
                    "source": "node-side-collector",
                },
            },
            {
                "eventId": "task-started-001",
                "eventType": "task_started",
                "occurredAt": utc_now(),
                "severity": "info",
                "title": "Task started",
                "detail": "Task task-local-001 started on local node",
                "taskId": "task-local-001",
                "agentId": "agent-main",
                "payload": {
                    "taskId": "task-local-001",
                    "agentId": "agent-main",
                    "nodeId": "node-local",
                    "taskType": "sample",
                    "source": "node-side-collector",
                },
            },
        ]
        return "\n".join(json.dumps(item, ensure_ascii=False) for item in sample_events) + "\n"
