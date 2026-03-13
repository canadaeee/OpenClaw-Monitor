# Backend

## Structure

```text
app/
  api.py
  collector.py
  db.py
  main.py
  models.py
  repository.py
  settings.py
  schemas.py
```

## Run

```bash
uvicorn app.main:app --host 127.0.0.1 --port 12888 --reload
```

Or use the helper scripts:

```bash
../scripts/init-backend.sh
../scripts/dev-backend.sh
```

On Windows:

```powershell
..\scripts\init-backend.ps1
..\scripts\dev-backend.ps1
```

## Current endpoints

- `/api/health`
- `/api/overview`
- `/api/agents`
- `/api/agents/{agent_id}`
- `/api/tasks`
- `/api/tasks/{task_id}`
- `/api/tasks/{task_id}/timeline`
- `/api/alerts`
- `/api/alerts/{alert_id}`
- `/api/events`
- `/api/events/raw`
- `/api/ingest/events`
- `/api/gateway/status`
- `/api/gateway/config`
- `/api/gateway/probe`
- `/api/gateway/ingest`
- `/api/gateway/stream`

## Modes

- Independent development mode:
  - Write events directly to `/api/ingest/events`
  - Suitable when OpenClaw is not running
- Gateway bridge mode:
  - Configure `config/gateway.json`
  - Probe OpenClaw gateway with `/api/gateway/probe`
  - Normalize gateway payloads through `/api/gateway/ingest`
  - When `enabled=true` and `auto_capture=true`, the backend starts background probing automatically
  - Default strategy is `local-first`, which probes local gateway candidates before any remote address
  - Default local port is `18789`; users with custom ports can extend `discovery_ports`
  - `/api/gateway/stream` now exposes a WebSocket subscription skeleton and runtime status

## Next steps

- Add JSONL replay/import tooling
- Add pagination for list queries
- Add real OpenClaw WebSocket subscription
- Add service installation for Ubuntu
