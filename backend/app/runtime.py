from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .collector import OpenClawCollector


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class GatewayRuntimeState:
    started: bool = False
    autoCaptureEnabled: bool = False
    detected: bool = False
    lastProbeAt: str | None = None
    lastSuccessAt: str | None = None
    lastError: str | None = None
    probeCount: int = 0
    lastResult: dict[str, Any] = field(default_factory=dict)


class GatewayRuntimeService:
    def __init__(self, collector: OpenClawCollector):
        self.collector = collector
        self.state = GatewayRuntimeState()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self.state.started = True
        self.state.autoCaptureEnabled = self.collector.settings.enabled and self.collector.settings.auto_capture
        if not self.state.autoCaptureEnabled:
            return
        self._task = asyncio.create_task(self._run(), name="openclaw-gateway-probe")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def reconfigure(self) -> None:
        await self.stop()
        self.state = GatewayRuntimeState(started=True)
        await self.start()

    def snapshot(self) -> dict[str, Any]:
        return {
            "started": self.state.started,
            "autoCaptureEnabled": self.state.autoCaptureEnabled,
            "detected": self.state.detected,
            "lastProbeAt": self.state.lastProbeAt,
            "lastSuccessAt": self.state.lastSuccessAt,
            "lastError": self.state.lastError,
            "probeCount": self.state.probeCount,
            "lastResult": self.state.lastResult,
        }

    async def _run(self) -> None:
        interval = max(5, int(self.collector.settings.probe_interval_seconds))
        while True:
            result = await asyncio.to_thread(self.collector.probe_http)
            self.state.lastProbeAt = utc_now()
            self.state.probeCount += 1
            self.state.lastResult = result
            self.state.detected = bool(result.get("reachable"))
            if self.state.detected:
                self.state.lastSuccessAt = self.state.lastProbeAt
                self.state.lastError = None
            else:
                self.state.lastError = str(result.get("reason", "unknown error"))
            await asyncio.sleep(interval)
