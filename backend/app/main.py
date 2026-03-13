from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import collector, router
from .db import init_db
from .gateway_manager import GatewayManager
from .runtime import GatewayRuntimeService
from .settings import ensure_gateway_config

init_db()
ensure_gateway_config()

runtime_service = GatewayRuntimeService(collector)
gateway_manager = GatewayManager(collector)


@asynccontextmanager
async def lifespan(_: FastAPI):
    from . import api

    api.runtime_service = runtime_service
    api.gateway_manager = gateway_manager
    await gateway_manager.start()
    try:
        yield
    finally:
        await gateway_manager.stop()


app = FastAPI(
    title="OpenClaw Monitor API",
    version="0.3.0",
    description="Read-only observability API for OpenClaw black-box visualization.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:12889",
        "http://127.0.0.1:12889",
        "http://localhost:12888",
        "http://127.0.0.1:12888",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)
