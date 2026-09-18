"""The single public VEXION beta model."""

from __future__ import annotations

from typing import Any, Dict, Optional

from lib import config

VEX_AI_ID = "vex-ai"
FREE_MODEL_ID = VEX_AI_ID

VEX_AI: Dict[str, Any] = {
    "id": VEX_AI_ID,
    "name": "VEX AI",
    "description": "VEXION's coding-first AI assistant",
    "tagline": "Build, debug and create with VEXION",
    "tier": 1,
    "provider": "groq",
    "vendor": "groq",
    "model": config.GROQ_MODEL,
    "costs": {"chat": 5, "coding": 20, "build": 50},
    "capabilities": ["chat", "markdown", "code", "math", "diagrams"],
}

CATALOG: Dict[str, Dict[str, Any]] = {VEX_AI_ID: VEX_AI}


def get_model(model_id: Optional[str] = None) -> Dict[str, Any]:
    if model_id and model_id != VEX_AI_ID:
        raise KeyError(model_id)
    return VEX_AI


def is_available(spec: Dict[str, Any]) -> bool:
    return bool(config.PROVIDER_KEY) and config.PROVIDER == "groq"


def operation_cost(model_id: Optional[str], operation: str) -> int:
    costs = get_model(model_id).get("costs", {})
    return int(costs.get(operation, costs["chat"]))


def public_catalog() -> list[Dict[str, Any]]:
    available = is_available(VEX_AI)
    return [{
        "id": VEX_AI_ID,
        "name": "VEX AI",
        "description": VEX_AI["description"],
        "tagline": VEX_AI["tagline"],
        "tier": 1,
        "requires_auth": False,
        "premium": False,
        "own_key": False,
        "provider": "groq",
        "provider_label": "VEXION AI",
        "icon": "spark",
        "vendor": "groq",
        "model": "vex-ai",
        "costs": VEX_AI["costs"],
        "capabilities": VEX_AI["capabilities"],
        "available": available,
        "unavailable_reason": "AI provider is not configured on the server." if not available else "",
    }]