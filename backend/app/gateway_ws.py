from __future__ import annotations

import asyncio
import contextlib
import json
import uuid
from dataclasses import dataclass
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
    note: str = "WebSocket subscription not started."


class OpenClawGatewayStream:
    def __init__(self, collector: OpenClawCollector):
        self.collector = collector
        self.state = GatewayStreamState()
        self._task: asyncio.Task | None = None

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
            enabled=bool(ws_url),
            note="WebSocket subscription is active; protocol mapping is still being refined.",
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
                "note": self.state.note,
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
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self.state.connected = False

    async def _run(self, ws_url: str, origin: str) -> None:
        try:
            import websockets
        except Exception as exc:  # pragma: no cover
            self.state.lastError = f"websockets unavailable: {exc}"
            self.state.note = "Install websockets dependency to enable live subscription."
            return

        headers = {}
        if self.collector.settings.token:
            headers["Authorization"] = f"Bearer {self.collector.settings.token}"

        try:
            connect_kwargs: dict[str, Any] = {"additional_headers": headers}
            if origin:
                connect_kwargs["origin"] = origin

            async with websockets.connect(ws_url, **connect_kwargs) as websocket:
                self.state.connected = True
                self.state.note = "Connected to OpenClaw Gateway WebSocket."
                await websocket.send(json.dumps(self._build_connect_request()))
                async for message in websocket:
                    self._handle_message(message)
        except Exception as exc:  # pragma: no cover
            self.state.connected = False
            self.state.lastError = str(exc)
            self.state.note = self._describe_error(str(exc))

    def _handle_message(self, message: Any) -> None:
        self.state.messagesReceived += 1
        self.state.lastMessageAt = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        try:
            payload = json.loads(message)
        except Exception:
            return

        if not isinstance(payload, dict):
            return

        if payload.get("type") == "res" and payload.get("ok") and isinstance(payload.get("payload"), dict):
            hello = payload["payload"]
            self.state.lastHello = hello
            return

        if payload.get("type") == "event" and isinstance(payload.get("payload"), dict):
            try:
                self.collector.ingest_gateway_event(payload["payload"])
            except Exception as exc:  # pragma: no cover
                self.state.lastError = f"ingest failed: {exc}"
            return

        if payload.get("type") == "res" and not payload.get("ok", True):
            self.state.lastError = str(payload.get("error") or "gateway rejected request")
            return

        try:
            self.collector.ingest_gateway_event(payload)
        except Exception as exc:  # pragma: no cover
            self.state.lastError = f"ingest failed: {exc}"

    def _build_connect_request(self) -> dict[str, Any]:
        token = self.collector.settings.token.strip()
        password = self.collector.settings.password.strip()
        params: dict[str, Any] = {
            "minProtocol": 3,
            "maxProtocol": 3,
            "client": {
                "id": "openclaw-control-ui",
                "version": "control-ui",
                "platform": "python",
                "mode": "webchat",
                "instanceId": f"monitor-{uuid.uuid4()}",
            },
            "role": "operator",
            "scopes": ["operator.admin", "operator.approvals", "operator.pairing"],
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
