from __future__ import annotations

from .collector import OpenClawCollector
from .gateway_ws import OpenClawGatewayStream
from .runtime import GatewayRuntimeService


class GatewayManager:
    def __init__(self, collector: OpenClawCollector):
        self.collector = collector
        self.runtime = GatewayRuntimeService(collector)
        self.stream = OpenClawGatewayStream(collector)

    async def start(self) -> None:
        await self.runtime.start()
        await self.stream.start()

    async def stop(self) -> None:
        await self.stream.stop()
        await self.runtime.stop()

    async def reconfigure(self, collector: OpenClawCollector) -> None:
        self.collector = collector
        self.runtime.collector = collector
        self.stream.collector = collector
        await self.stream.stop()
        await self.runtime.reconfigure()
        await self.stream.start()
