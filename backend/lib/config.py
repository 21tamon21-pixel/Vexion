"""VEXION runtime configuration."""

from __future__ import annotations

import os
from typing import Any, Dict


APP_NAME = os.environ.get("APP_NAME", "VEXION")
APP_TAGLINE = os.environ.get("APP_TAGLINE", "Build. Code. Create.")

PROVIDER = os.environ.get("VEXION_PROVIDER", "groq").strip().lower()
PROVIDER_KEY = os.environ.get("VEXION_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

DEFAULT_PERSONA = os.environ.get(
    "DEFAULT_PERSONA",
    "You are VEXION, a precise and capable AI coding assistant. "
    "Help the user understand ideas, solve problems, write and debug code, "
    "and build complete projects. Be accurate, practical and concise. "
    "Use GitHub-flavoured markdown and fenced code blocks with language tags. "
    "When the user asks for code, provide complete usable code rather than "
    "unnecessary fragments.",
)


def _flag(name: str, default: str = "true") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


FEATURES: Dict[str, bool] = {
    "voice_input": _flag("FEATURE_VOICE_INPUT"),
    "voice_output": _flag("FEATURE_VOICE_OUTPUT"),
    "vision": _flag("FEATURE_VISION", "false"),
    "web_search": _flag("FEATURE_WEB_SEARCH", "false"),
    "image_generation": _flag("FEATURE_IMAGE_GENERATION", "false"),
    "guest_mode": _flag("FEATURE_GUEST_MODE"),
}

WEEKLY_CREDIT_ALLOWANCE = 10_000
WAITLIST_START_NUMBER = max(1, int(os.environ.get("WAITLIST_START_NUMBER", "1000")))
BETA_RELEASE_DATE = os.environ.get("VEXION_BETA_RELEASE_DATE", "").strip()
BETA_STATUS = os.environ.get("VEXION_BETA_STATUS", "open").strip().lower()
BETA_MESSAGE = os.environ.get(
    "VEXION_BETA_MESSAGE",
    "A focused AI workspace for building, debugging and shipping code.",
).strip()


def public_config() -> Dict[str, Any]:
    from lib.models_catalog import FREE_MODEL_ID, public_catalog
    return {
        "app_name": APP_NAME,
        "app_tagline": APP_TAGLINE,
        "provider": PROVIDER,
        "model": GROQ_MODEL,
        "provider_ready": bool(PROVIDER_KEY) and PROVIDER == "groq",
        "features": FEATURES,
        "models": public_catalog(),
        "free_model_id": FREE_MODEL_ID,
        "weekly_credit_allowance": WEEKLY_CREDIT_ALLOWANCE,
        "beta": {
            "status": BETA_STATUS,
            "release_date": BETA_RELEASE_DATE,
            "message": BETA_MESSAGE,
        },
    }
