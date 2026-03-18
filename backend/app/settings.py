from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "gateway.json"
CONFIG_TEMPLATE_PATH = CONFIG_DIR / "gateway.example.json"


@dataclass
class GatewayCandidate:
    name: str
    base_url: str
    ws_url: str = ""
    origin: str = ""
    session_key: str = "agent:main:main"
    token: str = ""
    password: str = ""
    priority: int = 100


@dataclass
class GatewaySettings:
    enabled: bool = False
    auto_capture: bool = True
    probe_interval_seconds: int = 15
    mode: str = "local-first"
    default_port: int = 18789
    discovery_ports: list[int] | None = None
    base_url: str = ""
    ws_url: str = ""
    origin: str = ""
    session_key: str = "agent:main:main"
    token: str = ""
    password: str = ""
    language: str = "zh-CN"
    discovery_candidates: list[GatewayCandidate] | None = None


def load_gateway_settings() -> GatewaySettings:
    data: dict[str, object] = {}

    if CONFIG_PATH.exists():
      data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    base_url = _clean_string(os.getenv("OPENCLAW_GATEWAY_BASE_URL"), data.get("base_url", ""))
    token = _clean_string(os.getenv("OPENCLAW_GATEWAY_TOKEN"), data.get("token", ""))
    password = _clean_string(os.getenv("OPENCLAW_GATEWAY_PASSWORD"), data.get("password", ""))

    if os.getenv("OPENCLAW_GATEWAY_TOKEN") is None:
        openclaw_token = _load_openclaw_gateway_token()
        if openclaw_token and _is_localish_gateway_url(base_url):
            token = openclaw_token

    return GatewaySettings(
        enabled=_coerce_bool(os.getenv("OPENCLAW_GATEWAY_ENABLED"), data.get("enabled", False)),
        auto_capture=_coerce_bool(os.getenv("OPENCLAW_GATEWAY_AUTO_CAPTURE"), data.get("auto_capture", True)),
        probe_interval_seconds=int(os.getenv("OPENCLAW_GATEWAY_PROBE_INTERVAL", data.get("probe_interval_seconds", 15))),
        mode=_clean_string(os.getenv("OPENCLAW_GATEWAY_MODE"), data.get("mode", "local-first")),
        default_port=int(os.getenv("OPENCLAW_GATEWAY_DEFAULT_PORT", data.get("default_port", 18789))),
        discovery_ports=_load_ports(os.getenv("OPENCLAW_GATEWAY_DISCOVERY_PORTS"), data.get("discovery_ports")),
        base_url=base_url,
        ws_url=_clean_string(os.getenv("OPENCLAW_GATEWAY_WS_URL"), data.get("ws_url", "")),
        origin=_clean_string(os.getenv("OPENCLAW_GATEWAY_ORIGIN"), data.get("origin", "")),
        session_key=_clean_string(os.getenv("OPENCLAW_GATEWAY_SESSION_KEY"), data.get("session_key", "agent:main:main")),
        token=token,
        password=password,
        language=_clean_string(os.getenv("OPENCLAW_GATEWAY_LANGUAGE"), data.get("language", "zh-CN")),
        discovery_candidates=_load_candidates(data.get("discovery_candidates")),
    )


def ensure_gateway_config() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        template = _default_gateway_config()
        if CONFIG_TEMPLATE_PATH.exists():
            template = json.loads(CONFIG_TEMPLATE_PATH.read_text(encoding="utf-8"))
        CONFIG_PATH.write_text(
            json.dumps(template, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return CONFIG_PATH


def save_gateway_settings(payload: dict[str, Any]) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if CONFIG_PATH.exists():
        existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    next_data = {**existing, **payload}
    CONFIG_PATH.write_text(
        json.dumps(next_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return CONFIG_PATH


def settings_to_public_dict(settings: GatewaySettings) -> dict[str, Any]:
    data = asdict(settings)
    data["token"] = ""
    data["password"] = ""
    data["has_token"] = bool(settings.token)
    data["has_password"] = bool(settings.password)
    return data


def _coerce_bool(env_value: str | None, fallback: object) -> bool:
    if env_value is not None:
        return env_value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(fallback, bool):
        return fallback
    return str(fallback).strip().lower() in {"1", "true", "yes", "on"}


def _clean_string(env_value: str | None, fallback: object) -> str:
    value = env_value if env_value is not None else fallback
    text = str(value).strip()
    if text.lower() in {"none", "null"}:
        return ""
    return text


def _load_candidates(raw: object) -> list[GatewayCandidate]:
    if not isinstance(raw, list):
        return []

    candidates: list[GatewayCandidate] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        candidate = GatewayCandidate(
            name=str(item.get("name", "gateway")),
            base_url=str(item.get("base_url", "")),
            ws_url=str(item.get("ws_url", "")),
            origin=str(item.get("origin", "")),
            session_key=str(item.get("session_key", "agent:main:main")),
            token=str(item.get("token", "")),
            password=str(item.get("password", "")),
            priority=int(item.get("priority", 100)),
        )
        if candidate.base_url:
            candidates.append(candidate)

    return sorted(candidates, key=lambda item: item.priority)


def _load_ports(env_value: str | None, fallback: object) -> list[int]:
    if env_value is not None:
        raw_items = [item.strip() for item in env_value.split(",")]
    elif isinstance(fallback, list):
        raw_items = [str(item).strip() for item in fallback]
    else:
        raw_items = ["18789"]

    ports: list[int] = []
    for item in raw_items:
        if not item:
            continue
        try:
            port = int(item)
        except ValueError:
            continue
        if 1 <= port <= 65535 and port not in ports:
            ports.append(port)

    return ports or [18789]


def _default_gateway_config() -> dict[str, Any]:
    return {
        "enabled": True,
        "auto_capture": True,
        "probe_interval_seconds": 15,
        "mode": "local-first",
        "default_port": 18789,
        "discovery_ports": [18789],
        "base_url": "",
        "ws_url": "",
        "origin": "",
        "session_key": "agent:main:main",
        "token": "",
        "password": "",
        "language": "zh-CN",
        "discovery_candidates": [
            {
                "name": "remote-optional",
                "base_url": "https://example-openclaw.ts.net",
                "ws_url": "",
                "origin": "",
                "session_key": "agent:main:main",
                "token": "",
                "password": "",
                "priority": 100,
            },
        ],
    }


def _load_openclaw_gateway_token() -> str:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        return ""
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    gateway = payload.get("gateway")
    if not isinstance(gateway, dict):
        return ""
    auth = gateway.get("auth")
    if not isinstance(auth, dict):
        return ""
    token = auth.get("token")
    if not isinstance(token, str):
        return ""
    return token.strip()


def _is_localish_gateway_url(url: str) -> bool:
    value = url.strip().lower()
    if not value:
        return True
    return value.startswith("http://127.0.0.1") or value.startswith("http://localhost")
