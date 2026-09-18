"""VEXION AI provider layer.

VEXION currently uses Groq as its real AI provider.
The application talks to this abstraction rather than directly to Groq,
so another provider can be added later without rewriting the chat system.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional

import httpx

from lib import config


class ChatProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def stream(
        self,
        system: str,
        history: List[Dict[str, str]],
        model: str = "",
        images: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError


class GroqProvider(ChatProvider):
    """Real streaming Groq provider."""

    name = "groq"

    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    async def stream(
        self,
        system: str,
        history: List[Dict[str, str]],
        model: str = "",
        images: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        if not config.PROVIDER_KEY:
            raise RuntimeError(
                "The configured AI provider is missing its server-side credential."
            )

        selected_model = model or config.GROQ_MODEL

        messages: List[Dict[str, object]] = [
            {
                "role": "system",
                "content": system,
            }
        ]

        for item in history:
            messages.append(
                {
                    "role": item["role"],
                    "content": item["content"],
                }
            )

        payload = {
            "model": selected_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
        }

        headers = {
            "Authorization": f"Bearer {config.PROVIDER_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=240) as http:
            async with http.stream(
                "POST",
                self.endpoint,
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code >= 300:
                    body = await response.aread()

                    try:
                        detail = json.loads(body).get("error", {}).get(
                            "message",
                            body.decode("utf-8", errors="replace"),
                        )
                    except Exception:
                        detail = body.decode(
                            "utf-8",
                            errors="replace",
                        )

                    raise RuntimeError(
                        f"Groq API error ({response.status_code}): {detail}"
                    )

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    chunk = line[6:].strip()

                    if chunk == "[DONE]":
                        break

                    try:
                        data = json.loads(chunk)
                        delta = (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                    except Exception:
                        continue

                    if delta:
                        yield delta


_PROVIDER = GroqProvider()


def get_provider(vendor: str = "") -> ChatProvider:
    """Return the configured provider, failing clearly when none is available."""

    if vendor not in {"", "groq"}:
        raise RuntimeError(f"Unsupported AI provider: {vendor}")

    if not config.PROVIDER_KEY or config.PROVIDER != "groq":
        raise RuntimeError(
            "VEXION's AI provider is not configured. "
            "Configure VEXION_PROVIDER=groq and VEXION_API_KEY on the server."
        )

    return _PROVIDER
