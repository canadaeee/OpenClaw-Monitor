from __future__ import annotations

import asyncio
import contextlib
import json
import os
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .collector import OpenClawCollector


@dataclass
class GatewaySubscriptionPlan:
    ws_url: str
    origin: str
    session_key: str
    enabled: bool
    note: str


@dataclass
class GatewayStreamState:
    started: bool = False
    connected: bool = False
    messagesReceived: int = 0
    lastMessageAt: str | None = None
    lastError: str | None = None
    activeWsUrl: str | None = None
    lastHello: dict[str, Any] | None = None
    lastHealthAt: str | None = None
    lastHealth: dict[str, Any] | None = None
    lastHealthSummary: dict[str, Any] | None = None
    lastUsageAt: str | None = None
    lastUsageStatus: Any | None = None
    lastUsageCost: Any | None = None
    lastUsageError: Any | None = None
    note: str = "WebSocket subscription not started."
    recentFrames: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=30))


class OpenClawGatewayStream:
    def __init__(self, collector: OpenClawCollector):
        self.collector = collector
        self.state = GatewayStreamState()
        self._task: asyncio.Task | None = None
        self._poll_task: asyncio.Task | None = None
        self._ws: Any | None = None
        self._send_lock = asyncio.Lock()

    def subscription_plan(self) -> GatewaySubscriptionPlan:
        first_reachable = self.collector.probe_http()
        ws_url = ""
        origin = ""
        if first_reachable.get("reachable"):
            ws_url = str(first_reachable.get("wsUrl", ""))
            origin = str(first_reachable.get("origin", "")) or self.collector.effective_origin
        return GatewaySubscriptionPlan(
            ws_url=ws_url,
            origin=origin,
            session_key=self.collector.settings.session_key,
            enabled=self.collector.settings.enabled,
            note="WebSocket enabled via settings." if self.collector.settings.enabled else "WebSocket disabled by settings.",
        )

    def describe(self) -> dict[str, Any]:
        plan = self.subscription_plan()
        return {
            "enabled": plan.enabled,
            "wsUrl": plan.ws_url,
            "origin": plan.origin,
            "sessionKey": plan.session_key,
            "note": plan.note,
            "runtime": {
                "started": self.state.started,
                "connected": self.state.connected,
                "messagesReceived": self.state.messagesReceived,
                "lastMessageAt": self.state.lastMessageAt,
                "lastError": self.state.lastError,
                "activeWsUrl": self.state.activeWsUrl,
                "lastHello": self.state.lastHello,
                "lastHealthAt": self.state.lastHealthAt,
                "lastHealthSummary": self.state.lastHealthSummary,
                "lastUsageAt": self.state.lastUsageAt,
                "lastUsageStatus": self.state.lastUsageStatus,
                "lastUsageCost": self.state.lastUsageCost,
                "lastUsageError": self.state.lastUsageError,
                "note": self.state.note,
                "recentFrames": list(self.state.recentFrames),
            },
        }

    async def start(self) -> None:
        self.state.started = True
        plan = self.subscription_plan()
        self.state.note = plan.note
        self.state.activeWsUrl = plan.ws_url or None
        if not plan.enabled:
            self.state.connected = False
            return
        self._task = asyncio.create_task(self._run(plan.ws_url, plan.origin), name="openclaw-gateway-stream")

    async def stop(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._poll_task
            self._poll_task = None
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self.state.connected = False
        self._ws = None

    async def _run(self, ws_url: str, origin: str) -> None:
        try:
            import websockets
        except Exception as exc:  # pragma: no cover
            self.state.lastError = f"websockets unavailable: {exc}"
            self.state.note = "Install websockets dependency to enable live subscription."
            return

        backoff_seconds = 1.0
        while True:
            headers: dict[str, str] = {}
            if self.collector.settings.token:
                headers["Authorization"] = f"Bearer {self.collector.settings.token}"

            try:
                connect_kwargs: dict[str, Any] = {"additional_headers": headers}
                if origin:
                    connect_kwargs["origin"] = origin

                async with websockets.connect(ws_url, **connect_kwargs) as websocket:
                    self._ws = websocket
                    self.state.connected = True
                    self.state.lastError = None
                    self.state.note = "Connected to OpenClaw Gateway WebSocket."
                    backoff_seconds = 1.0

                    await websocket.send(json.dumps(self._build_connect_request()))
                    async for message in websocket:
                        self._handle_message(message)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover
                self.state.connected = False
                self.state.lastError = str(exc)
                self.state.note = self._describe_error(str(exc))
            finally:
                self._ws = None
                if self._poll_task:
                    self._poll_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self._poll_task
                    self._poll_task = None

            # Reconnect loop (unless disabled)
            if not self.collector.settings.enabled:
                self.state.note = "WebSocket disabled by settings."
                self.state.connected = False
                return
            await asyncio.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2.0, 30.0)

    def _handle_message(self, message: Any) -> None:
        self.state.messagesReceived += 1
        self.state.lastMessageAt = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        try:
            payload = json.loads(message)
        except Exception:
            return

        if not isinstance(payload, dict):
            return

        inner_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else None
        self.state.recentFrames.append(
            {
                "at": self.state.lastMessageAt,
                "type": payload.get("type"),
                "id": payload.get("id"),
                "method": payload.get("method"),
                "event": payload.get("event") or (inner_payload.get("type") if inner_payload else None),
                "ok": payload.get("ok"),
                "payloadType": inner_payload.get("type") if inner_payload else None,
                "payloadKeys": sorted(list(inner_payload.keys()))[:12] if inner_payload else None,
                "keys": sorted(list(payload.keys()))[:12],
            }
        )

        if payload.get("type") == "res" and payload.get("ok") and isinstance(payload.get("payload"), dict):
            if payload["payload"].get("type") == "hello-ok":
                self.state.lastHello = payload["payload"]
                if self._poll_task is None and _usage_poll_enabled():
                    self._poll_task = asyncio.create_task(self._poll_usage(), name="openclaw-gateway-usage-poll")
                return

        if payload.get("type") == "event" and isinstance(payload.get("payload"), dict):
            inner = dict(payload["payload"])
            event_name = payload.get("event") or inner.get("type")
            if event_name and "type" not in inner:
                inner["type"] = event_name
            if event_name and "eventType" not in inner:
                inner["eventType"] = event_name
            if event_name == "health":
                self.state.lastHealthAt = self.state.lastMessageAt
                self.state.lastHealth = inner
                self.state.lastHealthSummary = self._summarize_health(inner)
            try:
                self.collector.ingest_gateway_event(inner)
            except Exception as exc:  # pragma: no cover
                self.state.lastError = f"ingest failed: {exc}"
            return

        if payload.get("type") == "res" and not payload.get("ok", True):
            request_id = payload.get("id") if isinstance(payload.get("id"), str) else ""
            error_payload = payload.get("error") or "gateway rejected request"
            self.state.lastError = str(error_payload)
            if request_id.startswith("usage.status:") or request_id.startswith("usage.cost:"):
                self.state.lastUsageAt = self.state.lastMessageAt
                self.state.lastUsageError = error_payload
            return

        if payload.get("type") == "res" and payload.get("ok") and isinstance(payload.get("id"), str):
            self._handle_response(str(payload.get("id")), payload.get("payload"))
            return

        try:
            self.collector.ingest_gateway_event(payload)
        except Exception as exc:  # pragma: no cover
            self.state.lastError = f"ingest failed: {exc}"

    def _handle_response(self, request_id: str, response_payload: Any) -> None:
        if request_id.startswith("usage.status:"):
            self.state.lastUsageAt = self.state.lastMessageAt
            self.state.lastUsageStatus = response_payload
            return
        if request_id.startswith("usage.cost:"):
            self.state.lastUsageAt = self.state.lastMessageAt
            self.state.lastUsageCost = response_payload
            return

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> None:
        if not self._ws or not self.state.connected:
            return
        request_id = f"{method}:{uuid.uuid4()}"
        frame: dict[str, Any] = {"type": "req", "id": request_id, "method": method}
        if params is not None:
            frame["params"] = params
        async with self._send_lock:
            try:
                await self._ws.send(json.dumps(frame))
            except Exception as exc:  # pragma: no cover
                self.state.lastError = f"send failed: {exc}"

    async def _poll_usage(self) -> None:
        while True:
            # Best-effort: gateway will ignore/deny unsupported calls.
            await self._send_request("usage.status")
            await asyncio.sleep(1)
            await self._send_request("usage.cost")
            await asyncio.sleep(15)

    def _build_connect_request(self) -> dict[str, Any]:
        token = self.collector.settings.token.strip()
        password = self.collector.settings.password.strip()
        params: dict[str, Any] = {
            "minProtocol": 3,
            "maxProtocol": 3,
                "client": {
                    "id": "gateway-client",
                    "version": "openclaw-monitor/1.1.1",
                    "platform": "python",
                    "mode": "backend",
                    "instanceId": f"monitor-{uuid.uuid4()}",
                },
            "role": "operator",
            "scopes": ["operator.read", "operator.admin"],
            "caps": ["tool-events"],
            "userAgent": "OpenClaw Monitor Backend",
            "locale": self.collector.settings.language,
        }
        if token or password:
            auth: dict[str, str] = {}
            if token:
                auth["token"] = token
            if password:
                auth["password"] = password
            params["auth"] = auth

        return {
            "type": "req",
            "id": f"connect-{uuid.uuid4()}",
            "method": "connect",
            "params": params,
        }

    def _describe_error(self, message: str) -> str:
        lowered = message.lower()
        if "origin not allowed" in lowered:
            return "Gateway 拒绝了当前 Origin，请在 Gateway 设置中补充允许的来源或手动指定 Origin。"
        if "device identity" in lowered or "secure context" in lowered:
            return "Gateway 需要设备身份或 token/password 认证；请在 HTTPS/localhost 环境下运行，或在 Gateway 设置中补充认证信息。"
        if "auth" in lowered or "token" in lowered or "password" in lowered:
            return "Gateway 需要认证，请在 Gateway 设置中填写 token 或 password。"
        return "WebSocket connection failed."

    def _summarize_health(self, payload: dict[str, Any]) -> dict[str, Any]:
        agents = payload.get("agents")
        sessions = payload.get("sessions")
        channels = payload.get("channels")
        agent_summaries: list[dict[str, Any]] = []
        if isinstance(agents, list):
            for item in agents[:50]:
                if not isinstance(item, dict):
                    continue
                heartbeat = item.get("heartbeat")
                sessions_block = item.get("sessions")
                heartbeat_ts = None
                if isinstance(heartbeat, dict):
                    heartbeat_ts = heartbeat.get("ts") or heartbeat.get("timestamp")
                sessions_count = None
                last_session_updated_at = None
                if isinstance(sessions_block, dict):
                    sessions_count = sessions_block.get("count")
                    recent = sessions_block.get("recent")
                    if isinstance(recent, list):
                        for entry in recent:
                            if not isinstance(entry, dict):
                                continue
                            updated_at = entry.get("updatedAt")
                            if isinstance(updated_at, (int, float)):
                                last_session_updated_at = (
                                    updated_at
                                    if last_session_updated_at is None
                                    else max(last_session_updated_at, updated_at)
                                )
                agent_summaries.append(
                    {
                        "agentId": item.get("agentId"),
                        "isDefault": item.get("isDefault"),
                        "heartbeatTs": heartbeat_ts,
                        "lastSessionUpdatedAt": last_session_updated_at,
                        "sessionsCount": sessions_count,
                    }
                )
        return {
            "ok": payload.get("ok"),
            "ts": payload.get("ts"),
            "agentCount": len(agents) if isinstance(agents, list) else None,
            "sessionCount": (
                len(sessions)
                if isinstance(sessions, list)
                else sessions.get("count")
                if isinstance(sessions, dict)
                else None
            ),
            "channelCount": len(channels) if isinstance(channels, dict) else len(channels) if isinstance(channels, list) else None,
            "heartbeatSeconds": payload.get("heartbeatSeconds"),
            "durationMs": payload.get("durationMs"),
            "defaultAgentId": payload.get("defaultAgentId"),
            "agents": agent_summaries,
        }


def _usage_poll_enabled() -> bool:
    return os.getenv("OPENCLAW_MONITOR_GATEWAY_USAGE_POLL", "").strip().lower() in {"1", "true", "yes", "on"}
