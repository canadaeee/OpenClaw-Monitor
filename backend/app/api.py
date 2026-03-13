from fastapi import APIRouter, HTTPException

from . import repository
from .collector import OpenClawCollector
from .gateway_ws import OpenClawGatewayStream
from .node_collector import NodeCollectorRuntimeService, NodeSideCollector
from .schemas import GatewayConfigUpdate, IngestEvent, NodeCollectorIngestFileRequest
from .settings import load_gateway_settings, save_gateway_settings, settings_to_public_dict
from .versioning import get_update_status

router = APIRouter(prefix="/api")
collector = OpenClawCollector(load_gateway_settings())
gateway_stream = OpenClawGatewayStream(collector)
node_collector = NodeSideCollector(collector)
node_collector_runtime = NodeCollectorRuntimeService(node_collector)
runtime_service = None
gateway_manager = None


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "openclaw-monitor-api", "time": repository.utc_now()}


@router.get("/system/update-status")
def system_update_status() -> dict:
    return get_update_status()


@router.get("/overview")
def overview() -> dict:
    return repository.get_overview()


@router.get("/agents")
def agents() -> dict:
    items = repository.list_agents()
    return {"items": items, "page": 1, "page_size": 20, "total": len(items)}


@router.get("/agents/{agent_id}")
def agent_detail(agent_id: str) -> dict:
    item = repository.get_agent(agent_id)
    if not item:
        raise HTTPException(status_code=404, detail="Agent not found")
    return item


@router.get("/tasks")
def tasks() -> dict:
    items = repository.list_tasks()
    return {"items": items, "page": 1, "page_size": 20, "total": len(items)}


@router.get("/tasks/{task_id}")
def task_detail(task_id: str) -> dict:
    item = repository.get_task(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    return item


@router.get("/tasks/{task_id}/timeline")
def task_timeline(task_id: str) -> dict:
    item = repository.get_task(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="Task not found")
    timeline = repository.get_task_timeline(task_id)
    return {"items": timeline, "total": len(timeline)}


@router.get("/alerts")
def alerts() -> dict:
    items = repository.list_alerts()
    return {"items": items, "page": 1, "page_size": 20, "total": len(items)}


@router.get("/alerts/{alert_id}")
def alert_detail(alert_id: str) -> dict:
    item = repository.get_alert(alert_id)
    if not item:
        raise HTTPException(status_code=404, detail="Alert not found")
    return item


@router.get("/events")
def events(
    event_type: str | None = None,
    related_task_id: str | None = None,
    related_agent_id: str | None = None,
    severity: str | None = None,
) -> dict:
    items = repository.list_events(
        event_type=event_type,
        related_task_id=related_task_id,
        related_agent_id=related_agent_id,
        severity=severity,
    )
    return {"items": items, "page": 1, "page_size": 20, "total": len(items)}


@router.get("/events/raw")
def raw_events(
    event_type: str | None = None,
    task_id: str | None = None,
    agent_id: str | None = None,
) -> dict:
    items = repository.list_raw_events(
        event_type=event_type,
        task_id=task_id,
        agent_id=agent_id,
    )
    return {"items": items, "page": 1, "page_size": 20, "total": len(items)}


@router.post("/ingest/events")
def ingest_event(event: IngestEvent) -> dict:
    return repository.ingest_event(event)


@router.get("/gateway/status")
def gateway_status() -> dict:
    payload = {"config": collector.status()}
    if runtime_service is not None:
        payload["runtime"] = runtime_service.snapshot()
    return payload


@router.get("/gateway/config")
def gateway_config() -> dict:
    return settings_to_public_dict(collector.settings)


@router.put("/gateway/config")
async def update_gateway_config(config: GatewayConfigUpdate) -> dict:
    payload = config.model_dump()
    save_gateway_settings(payload)
    settings = load_gateway_settings()
    collector.update_settings(settings)
    gateway_stream.collector = collector
    node_collector.gateway_collector = collector
    if gateway_manager is not None:
        await gateway_manager.reconfigure(collector)
    elif runtime_service is not None:
        runtime_service.collector = collector
        await runtime_service.reconfigure()
    return {"saved": True, "config": settings_to_public_dict(settings)}


@router.get("/gateway/probe")
def gateway_probe() -> dict:
    return collector.probe_http()


@router.post("/gateway/ingest")
def gateway_ingest(payload: dict) -> dict:
    return collector.ingest_gateway_event(payload)


@router.get("/gateway/stream")
def gateway_stream_status() -> dict:
    return gateway_stream.describe()


@router.get("/node-collector/status")
def node_collector_status() -> dict:
    return node_collector.describe()


@router.get("/node-collector/sample")
def node_collector_sample() -> dict:
    return {
        "recommendedPath": node_collector.describe().get("recommendedPath"),
        "content": node_collector.sample_jsonl(),
    }


@router.post("/node-collector/ingest-file")
def node_collector_ingest_file(request: NodeCollectorIngestFileRequest) -> dict:
    results = node_collector.ingest_jsonl_file(request.path)
    return {
        "ingested": len(results),
        "path": request.path,
        "state": node_collector.describe(),
    }


@router.post("/node-collector/poll")
def node_collector_poll() -> dict:
    results = node_collector.poll_jsonl_file()
    return {
        "ingested": len(results),
        "state": node_collector.describe(),
    }
