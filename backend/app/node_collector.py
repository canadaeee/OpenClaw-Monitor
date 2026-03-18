from __future__ import annotations

import json
import asyncio
from collections import deque
from contextlib import suppress
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
    autoPolling: bool = False
    pollIntervalSeconds: int = 5
    lastFileOffset: int = 0


class NodeSideCollector:
    def __init__(self, gateway_collector: OpenClawCollector, config: NodeCollectorConfig | None = None):
        self.gateway_collector = gateway_collector
        self.config = config or NodeCollectorConfig()
        self.state = NodeCollectorState(
            enabled=self.config.enabled,
            mode=self.config.mode,
            source_type=self.config.source_type,
            source_path=self.config.source_path,
            autoPolling=self.config.enabled,
            pollIntervalSeconds=self.config.poll_interval_seconds,
        )
        self._offsets: dict[str, int] = {}

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
            "autoPolling": self.state.autoPolling,
            "pollIntervalSeconds": self.state.pollIntervalSeconds,
            "lastFileOffset": self.state.lastFileOffset,
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

    def _poll_single_file(self, file_path: Path) -> list[dict[str, Any]]:
        if not file_path.exists():
            return []
        offset = self._offsets.get(str(file_path), 0)
        file_size = file_path.stat().st_size
        if file_size < offset:
            offset = 0
        results: list[dict[str, Any]] = []
        with file_path.open("r", encoding="utf-8") as handle:
            handle.seek(offset)
            results = self.ingest_lines(handle)
            self._offsets[str(file_path)] = handle.tell()
        if results:
            self.state.lastError = None
        return results

    def poll_jsonl_file(self, path: str | Path | None = None) -> list[dict[str, Any]]:
        base_path = Path(path or self.state.source_path or self.describe()["recommendedPath"])
        self.state.source_path = str(base_path)
        results: list[dict[str, Any]] = []

        if base_path.is_dir():
            # Poll all agent sessions/*.jsonl under the directory
            for agent_dir in base_path.iterdir():
                if not agent_dir.is_dir():
                    continue
                sessions_dir = agent_dir / "sessions"
                if sessions_dir.exists():
                    for jsonl_file in sessions_dir.glob("*.jsonl"):
                        results.extend(self._poll_single_file(jsonl_file))
                    results.extend(self._poll_sessions_index(agent_dir, sessions_dir))
        else:
            results.extend(self._poll_single_file(base_path))

        # Update aggregate state
        if results:
            self.state.ingestedCount += len(results)
            self.state.lastReadAt = utc_now()
            self.state.lastIngestAt = utc_now()
        return results

    def _poll_sessions_index(self, agent_dir: Path, sessions_dir: Path) -> list[dict[str, Any]]:
        index_path = sessions_dir / "sessions.json"
        if not index_path.exists():
            return []
        agent_id = agent_dir.name
        pricing = _load_pricing_config()
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.state.lastError = f"failed to read sessions.json for {agent_id}: {exc}"
            return []
        if not isinstance(raw, dict):
            return []

        results: list[dict[str, Any]] = []
        for session_key, session_info in raw.items():
            if not isinstance(session_key, str) or not session_key.strip():
                continue
            if not isinstance(session_info, dict):
                continue
            updated_at_ms = session_info.get("updatedAt")
            if not isinstance(updated_at_ms, (int, float)):
                continue
            updated_at = _utc_from_epoch(updated_at_ms)

            input_tokens = _int(session_info.get("inputTokens") or session_info.get("input") or 0)
            output_tokens = _int(session_info.get("outputTokens") or session_info.get("output") or 0)
            cache_read = _int(session_info.get("cacheRead") or 0)
            cache_write = _int(session_info.get("cacheWrite") or 0)
            computed_total = input_tokens + output_tokens + cache_read + cache_write
            reported_total = max(
                _int(session_info.get("totalTokensFresh") or 0),
                _int(session_info.get("totalTokens") or 0),
                _int(session_info.get("total") or 0),
            )
            # Prefer the larger total to avoid "stuck" counters when OpenClaw updates only one side.
            total_tokens = max(computed_total, reported_total)
            model_provider = session_info.get("modelProvider")
            model_id = session_info.get("model")

            session_id = session_info.get("sessionId")
            session_file = session_info.get("sessionFile")
            file_path = None
            if isinstance(session_file, str) and session_file.strip():
                file_path = Path(session_file)
            elif isinstance(session_id, str) and session_id.strip():
                file_path = sessions_dir / f"{session_id}.jsonl"

            estimated_cost = 0.0
            currency = "USD"
            cost_breakdown = None
            cost_source = None

            # Prefer observed cost embedded in OpenClaw session logs (when available).
            observed_cost_total = None
            observed_cost_breakdown = None
            if file_path is not None:
                observed_cost_total, observed_cost_breakdown = _derive_session_cost_total(file_path)
            if observed_cost_total is not None:
                estimated_cost = float(observed_cost_total)
                currency = "USD"
                cost_breakdown = observed_cost_breakdown
                cost_source = "session-log"
            elif pricing is not None:
                estimated_cost, currency, cost_breakdown = _estimate_cost_from_pricing(
                    pricing,
                    provider=str(model_provider) if isinstance(model_provider, str) else "",
                    model=str(model_id) if isinstance(model_id, str) else "",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read=cache_read,
                    cache_write=cache_write,
                )
                cost_source = "pricing"

            # Derive duration from session file (best-effort).
            duration_ms = None
            started_at = None
            ended_at = None
            if file_path is not None:
                started_at, ended_at, duration_ms = _derive_session_duration(file_path)

            payload = {
                "eventId": f"token-snapshot:{agent_id}:{session_key}:{int(updated_at_ms)}:{total_tokens}:{input_tokens}:{output_tokens}:{cache_read}:{cache_write}:{int(duration_ms or 0)}:{int(round(float(estimated_cost) * 1_000_000))}:{cost_source or 'none'}",
                "eventType": "token_snapshot",
                "occurredAt": updated_at,
                "severity": "info",
                "title": "Token snapshot",
                "detail": f"{agent_id} {session_key} tokens={total_tokens}",
                "taskId": session_key,
                "agentId": agent_id,
                "payload": {
                    "agentId": agent_id,
                    "sessionKey": session_key,
                    "updatedAtMs": int(updated_at_ms),
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": total_tokens,
                    "cacheRead": cache_read,
                    "cacheWrite": cache_write,
                    "reportedTotalTokens": reported_total,
                    "estimatedCost": estimated_cost,
                    "currency": currency,
                    "costBreakdown": cost_breakdown,
                    "costSource": cost_source,
                    "modelProvider": model_provider,
                    "model": model_id,
                    "chatType": session_info.get("chatType"),
                    "origin": session_info.get("origin"),
                    "sessionId": session_id,
                    "startedAt": started_at,
                    "endedAt": ended_at,
                    "durationMs": duration_ms,
                },
            }
            try:
                results.append(self.ingest_payload(payload))
            except Exception as exc:
                self.state.lastError = f"ingest sessions.json failed: {exc}"

        return results

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


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _utc_from_epoch(epoch: float) -> str:
    seconds = epoch / 1000 if epoch > 1e12 else epoch
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _extract_timestamp(obj: dict[str, Any]) -> datetime | None:
    dt = _parse_iso_datetime(obj.get("timestamp"))
    if dt:
        return dt
    message = obj.get("message")
    if isinstance(message, dict):
        dt = _parse_iso_datetime(message.get("timestamp"))
        if dt:
            return dt
    return None


_SESSION_COST_CACHE: dict[str, tuple[float, int, float | None, dict[str, float] | None]] = {}


def _extract_usage_cost(obj: dict[str, Any]) -> tuple[float | None, dict[str, float] | None]:
    usage = obj.get("usage")
    if not isinstance(usage, dict):
        message = obj.get("message")
        if isinstance(message, dict):
            usage = message.get("usage")
    if not isinstance(usage, dict):
        payload = obj.get("payload")
        if isinstance(payload, dict):
            usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None, None

    cost = usage.get("cost")
    if isinstance(cost, (int, float)):
        return float(cost), None
    if not isinstance(cost, dict):
        return None, None

    input_cost = _float(cost.get("input"))
    output_cost = _float(cost.get("output"))
    cache_read_cost = _float(cost.get("cacheRead"))
    cache_write_cost = _float(cost.get("cacheWrite"))
    total_cost = cost.get("total")
    total = _float(total_cost) if total_cost is not None else input_cost + output_cost + cache_read_cost + cache_write_cost

    breakdown = {
        "input": input_cost,
        "output": output_cost,
        "cacheRead": cache_read_cost,
        "cacheWrite": cache_write_cost,
        "total": total,
    }
    # Distinguish "present but zero" from "absent".
    if any(value != 0.0 for value in breakdown.values()):
        return total, breakdown
    return 0.0, breakdown


def _derive_session_cost_total(path: Path) -> tuple[float | None, dict[str, float] | None]:
    if not path.exists() or not path.is_file():
        return None, None
    try:
        stat = path.stat()
    except Exception:
        return None, None
    cache_key = str(path)
    cached = _SESSION_COST_CACHE.get(cache_key)
    if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
        return cached[2], cached[3]

    found_any = False
    total = 0.0
    breakdown_sum = {"input": 0.0, "output": 0.0, "cacheRead": 0.0, "cacheWrite": 0.0, "total": 0.0}
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if not isinstance(obj, dict):
                    continue
                cost_total, breakdown = _extract_usage_cost(obj)
                if cost_total is None and breakdown is None:
                    continue
                found_any = True
                total += float(cost_total or 0.0)
                if isinstance(breakdown, dict):
                    for key in breakdown_sum:
                        breakdown_sum[key] += _float(breakdown.get(key))
    except Exception:
        _SESSION_COST_CACHE[cache_key] = (stat.st_mtime, stat.st_size, None, None)
        return None, None

    if not found_any:
        _SESSION_COST_CACHE[cache_key] = (stat.st_mtime, stat.st_size, None, None)
        return None, None
    _SESSION_COST_CACHE[cache_key] = (stat.st_mtime, stat.st_size, total, breakdown_sum)
    return total, breakdown_sum


def _derive_session_duration(path: Path) -> tuple[str | None, str | None, int | None]:
    if not path.exists() or not path.is_file():
        return None, None, None
    start_dt: datetime | None = None
    end_dt: datetime | None = None

    # Read first few lines to locate a reasonable start timestamp.
    try:
        with path.open("r", encoding="utf-8") as handle:
            for _ in range(200):
                line = handle.readline()
                if not line:
                    break
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if not isinstance(obj, dict):
                    continue
                dt = _extract_timestamp(obj)
                if dt is not None:
                    start_dt = dt
                    break
    except Exception:
        return None, None, None

    # Read tail (last N lines) to locate end timestamp.
    tail: deque[str] = deque(maxlen=250)
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                tail.append(line)
    except Exception:
        return None, None, None

    for line in reversed(tail):
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        dt = _extract_timestamp(obj)
        if dt is not None:
            end_dt = dt
            break

    if start_dt is None or end_dt is None:
        return None, None, None
    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt
    duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
    started_at = start_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    ended_at = end_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return started_at, ended_at, duration_ms


_PRICING_CACHE: tuple[float, dict[str, Any]] | None = None


def _load_pricing_config() -> dict[str, Any] | None:
    global _PRICING_CACHE
    base_dir = Path(__file__).resolve().parents[2]
    path = base_dir / "config" / "pricing.json"
    if not path.exists():
        _PRICING_CACHE = None
        return None
    mtime = path.stat().st_mtime
    if _PRICING_CACHE and _PRICING_CACHE[0] == mtime:
        return _PRICING_CACHE[1]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _PRICING_CACHE = None
        return None
    if not isinstance(payload, dict):
        _PRICING_CACHE = None
        return None
    _PRICING_CACHE = (mtime, payload)
    return payload


def _estimate_cost_from_pricing(
    pricing: dict[str, Any],
    *,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read: int,
    cache_write: int,
) -> tuple[float, str, dict[str, Any] | None]:
    table = pricing.get("providers") if isinstance(pricing.get("providers"), dict) else {}
    provider_table = table.get(provider) if isinstance(table, dict) else None
    model_table = provider_table.get(model) if isinstance(provider_table, dict) else None
    if not isinstance(model_table, dict):
        return 0.0, "USD", None
    currency = model_table.get("currency") if isinstance(model_table.get("currency"), str) else "USD"
    per_1m = model_table.get("per1M") if isinstance(model_table.get("per1M"), dict) else {}
    price_in = float(per_1m.get("input") or 0.0)
    price_out = float(per_1m.get("output") or 0.0)
    price_cr = float(per_1m.get("cacheRead") or 0.0)
    price_cw = float(per_1m.get("cacheWrite") or 0.0)

    cost_in = (input_tokens / 1_000_000.0) * price_in
    cost_out = (output_tokens / 1_000_000.0) * price_out
    cost_cr = (cache_read / 1_000_000.0) * price_cr
    cost_cw = (cache_write / 1_000_000.0) * price_cw
    total = cost_in + cost_out + cost_cr + cost_cw
    return (
        total,
        currency,
        {
            "input": cost_in,
            "output": cost_out,
            "cacheRead": cost_cr,
            "cacheWrite": cost_cw,
            "total": total,
            "per1M": {"input": price_in, "output": price_out, "cacheRead": price_cr, "cacheWrite": price_cw},
        },
    )


class NodeCollectorRuntimeService:
    def __init__(self, collector: NodeSideCollector):
        self.collector = collector
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not self.collector.state.enabled:
            return
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="openclaw-node-collector")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _run(self) -> None:
        interval = max(2, int(self.collector.config.poll_interval_seconds))
        while True:
            await asyncio.to_thread(self.collector.poll_jsonl_file)
            await asyncio.sleep(interval)
