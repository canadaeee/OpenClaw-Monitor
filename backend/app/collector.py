from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .repository import ingest_event
from .schemas import IngestEvent
from .settings import GatewayCandidate, GatewaySettings


class OpenClawCollector:
    def __init__(self, settings: GatewaySettings):
        self.settings = settings

    def update_settings(self, settings: GatewaySettings) -> None:
        self.settings = settings

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.settings.enabled,
            "autoCapture": self.settings.auto_capture,
            "probeIntervalSeconds": self.settings.probe_interval_seconds,
            "mode": self.settings.mode,
            "defaultPort": self.settings.default_port,
            "discoveryPorts": self.settings.discovery_ports or [],
            "baseUrl": self.settings.base_url,
            "wsUrl": self.effective_ws_url,
            "origin": self.effective_origin,
            "sessionKey": self.settings.session_key,
            "hasToken": bool(self.settings.token),
            "language": self.settings.language,
            "candidateCount": len(self.candidates),
        }

    @property
    def effective_ws_url(self) -> str:
        if self.settings.ws_url:
            return self.settings.ws_url
        if self.settings.base_url.startswith("https://"):
            return "wss://" + self.settings.base_url.removeprefix("https://")
        if self.settings.base_url.startswith("http://"):
            return "ws://" + self.settings.base_url.removeprefix("http://")
        return ""

    @property
    def effective_origin(self) -> str:
        if self.settings.origin:
            return self.settings.origin
        if self.settings.base_url:
            return self.settings.base_url.rstrip("/")
        return ""

    @property
    def candidates(self) -> list[GatewayCandidate]:
        explicit = []
        if self.settings.base_url:
            explicit.append(
                GatewayCandidate(
                    name="explicit",
                    base_url=self.settings.base_url,
                    ws_url=self.settings.ws_url,
                    origin=self.settings.origin,
                    session_key=self.settings.session_key,
                    token=self.settings.token,
                    password=self.settings.password,
                    priority=0,
                )
            )
        return explicit + self._local_candidates() + (self.settings.discovery_candidates or [])

    def probe_http(self) -> dict[str, Any]:
        if not self.candidates:
            return {"reachable": False, "reason": "no gateway candidates configured"}

        failures: list[dict[str, str]] = []
        for candidate in self.candidates:
            request = Request(
                candidate.base_url,
                headers=self._headers(candidate),
                method="GET",
            )

            try:
                with urlopen(request, timeout=5) as response:
                    return {
                        "reachable": True,
                        "status": response.status,
                        "url": candidate.base_url,
                        "name": candidate.name,
                        "wsUrl": self._resolve_ws_url(candidate),
                        "origin": self.resolve_origin(candidate),
                    }
            except HTTPError as exc:
                failures.append({"name": candidate.name, "url": candidate.base_url, "reason": f"http {exc.code}"})
            except URLError as exc:
                failures.append({"name": candidate.name, "url": candidate.base_url, "reason": str(exc.reason)})

        return {"reachable": False, "reason": "all candidates failed", "failures": failures}

    def normalize_gateway_event(self, payload: dict[str, Any]) -> IngestEvent:
        event_id = str(payload.get("eventId") or payload.get("id") or "gateway-event")
        event_type = str(payload.get("eventType") or payload.get("type") or "gateway_event")
        occurred_at = str(payload.get("occurredAt") or payload.get("timestamp") or payload.get("createdAt"))
        severity = str(payload.get("severity") or "info")
        title = str(payload.get("title") or payload.get("name") or event_type)
        detail = str(payload.get("detail") or payload.get("message") or "OpenClaw gateway event")

        return IngestEvent(
            eventId=event_id,
            eventType=event_type,
            occurredAt=occurred_at,
            severity=severity,
            title=title,
            detail=detail,
            taskId=_maybe_str(payload.get("taskId") or payload.get("task_id")),
            agentId=_maybe_str(payload.get("agentId") or payload.get("agent_id")),
            alertId=_maybe_str(payload.get("alertId") or payload.get("alert_id")),
            payload=payload,
        )

    def ingest_gateway_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = self.normalize_gateway_event(payload)
        return ingest_event(event)

    def export_config_view(self) -> dict[str, Any]:
        public = asdict(self.settings)
        public["token"] = ""
        public["password"] = ""
        public["has_token"] = bool(self.settings.token)
        public["has_password"] = bool(self.settings.password)
        public["ws_url"] = self.effective_ws_url
        public["origin"] = self.effective_origin
        return public

    def _headers(self, candidate: GatewayCandidate | None = None) -> dict[str, str]:
        headers = {"Accept": "text/html,application/json"}
        token = candidate.token if candidate and candidate.token else self.settings.token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _resolve_ws_url(self, candidate: GatewayCandidate) -> str:
        if candidate.ws_url:
            return candidate.ws_url
        if candidate.base_url.startswith("https://"):
            return "wss://" + candidate.base_url.removeprefix("https://")
        if candidate.base_url.startswith("http://"):
            return "ws://" + candidate.base_url.removeprefix("http://")
        return ""

    def resolve_origin(self, candidate: GatewayCandidate | None = None) -> str:
        if candidate and candidate.origin:
            return candidate.origin.rstrip("/")
        if candidate and candidate.base_url:
            return candidate.base_url.rstrip("/")
        return self.effective_origin

    def _local_candidates(self) -> list[GatewayCandidate]:
        ports = self.settings.discovery_ports or [self.settings.default_port]
        candidates: list[GatewayCandidate] = []
        priority = 10
        for host in ("127.0.0.1", "localhost"):
            for port in ports:
                candidates.append(
                    GatewayCandidate(
                        name=f"local-{host}-{port}",
                        base_url=f"http://{host}:{port}",
                        ws_url=f"ws://{host}:{port}",
                        origin=f"http://{host}:{port}",
                        session_key=self.settings.session_key,
                        token=self.settings.token,
                        password=self.settings.password,
                        priority=priority,
                    )
                )
                priority += 10
        return candidates


def _maybe_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
