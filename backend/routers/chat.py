"""VEXION chat streaming endpoint."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from lib import config
from lib.db import db
from lib.models_catalog import (
    FREE_MODEL_ID,
    get_model,
    is_available,
    operation_cost,
)
from lib.providers import get_provider
from lib.security import current_user
from routers.usage import ensure_credit_state
from models.schemas import AttachmentRef, Message, Persona, SendMessageRequest

router = APIRouter(prefix="/chat", tags=["chat"])

MAX_HISTORY = 40


class GuestTurn(BaseModel):
    role: str
    content: str


class GuestStreamRequest(BaseModel):
    content: str = Field(min_length=1)
    history: List[GuestTurn] = Field(default_factory=list)


def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _build_system(persona: Persona) -> str:
    parts = [
        config.DEFAULT_PERSONA,
        f"Tone: {persona.tone}. Verbosity: {persona.verbosity}.",
    ]

    if persona.system_prompt.strip():
        parts.append(
            "Operator directives: " + persona.system_prompt.strip()
        )

    return "\n\n".join(parts)


def _resolve_model(model_id: str | None, *, authenticated: bool = False, user: Dict[str, Any] | None = None) -> Dict[str, Any]:
    try:
        spec = get_model(model_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown VEXION model: {model_id}",
        ) from exc

    if not is_available(spec):
        raise HTTPException(
            status_code=503,
            detail=(
                "VEXION's AI provider is not configured. "
                "Configure VEXION_PROVIDER=groq and VEXION_API_KEY on the server."
            ),
        )

    return spec


def _credit_state(user: Dict[str, Any]) -> Dict[str, Any]:
    state = user.get("credits") or {}

    return {
        "allowance": int(
            state.get(
                "allowance",
                config.WEEKLY_CREDIT_ALLOWANCE,
            )
        ),
        "used": int(state.get("used", 0)),
        "remaining": int(
            state.get(
                "remaining",
                config.WEEKLY_CREDIT_ALLOWANCE,
            )
        ),
    }


async def _reserve_credits(
    user: Dict[str, Any],
    cost: int,
) -> Dict[str, Any]:
    """Atomically reserve credits before starting an AI request."""

    now = datetime.now(timezone.utc)

    current = await db.users.find_one(
        {"id": user["id"]},
        {"credits": 1},
    )

    if current is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Make sure the user's weekly allowance is current
    # before attempting to reserve credits.
    current_state = await ensure_credit_state({
        "id": user["id"],
        "credits": current.get("credits"),
    })

    state = current_state

    allowance = int(
        state.get(
            "allowance",
            config.WEEKLY_CREDIT_ALLOWANCE,
        )
    )
    used = int(state.get("used", 0))
    remaining = int(
        state.get(
            "remaining",
            allowance - used,
        )
    )

    if remaining < cost:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "You do not have enough weekly credits.",
                "required": cost,
                "remaining": max(0, remaining),
                "allowance": allowance,
                "reset_at": state.get("reset_at"),
            },
        )

    new_used = used + cost
    new_remaining = max(0, allowance - new_used)

    updated = await db.users.find_one_and_update(
        {
            "id": user["id"],
            "$or": [
                {"credits.used": used},
                {"credits": {"$exists": False}},
            ],
        },
        {
            "$set": {
                "credits.allowance": allowance,
                "credits.used": new_used,
                "credits.remaining": new_remaining,
                "credits.updated_at": now,
            }
        },
        return_document=True,
    )

    if not updated:
        raise HTTPException(
            status_code=409,
            detail="Credit balance changed. Please try again.",
        )

    return {
        "allowance": allowance,
        "used": new_used,
        "remaining": new_remaining,
        "cost": cost,
    }


async def _load_attachments(
    ids: List[str],
    user_id: str,
) -> tuple[List[str], str, List[Dict[str, str]]]:
    images: List[str] = []
    doc_text: List[str] = []
    refs: List[Dict[str, str]] = []

    for aid in ids[:6]:
        doc = await db.attachments.find_one({"id": aid})

        if not doc:
            continue

        owner = doc.get("user_id")

        if owner and owner != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not your attachment",
            )

        refs.append(
            {
                "id": doc["id"],
                "kind": doc["kind"],
                "filename": doc["filename"],
            }
        )

        if doc["kind"] == "image" and doc.get("data_url"):
            images.append(
                doc["data_url"].split(",", 1)[-1]
            )

        elif doc.get("extracted_text"):
            doc_text.append(
                f"### ATTACHED DOCUMENT: {doc['filename']}\n"
                f"{doc['extracted_text'][:60000]}"
            )

    return images, "\n\n".join(doc_text), refs


@router.post("/guest/stream")
async def stream_guest(payload: GuestStreamRequest):
    """Guest streaming.

    Guest conversations are intentionally not persisted.
    """

    spec = _resolve_model(FREE_MODEL_ID, authenticated=False)

    system = _build_system(Persona()) + (
        "\n\nThis is a guest session. "
        "Do not claim to remember information after this session."
    )

    history = [
        {
            "role": item.role,
            "content": item.content,
        }
        for item in payload.history[-MAX_HISTORY:]
    ]

    history.append(
        {
            "role": "user",
            "content": payload.content,
        }
    )

    try:
        provider = get_provider()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    message_id = Message(
        conversation_id="guest",
        role="assistant",
        content="",
    ).id

    async def generator() -> AsyncIterator[str]:
        yield _sse(
            "start",
            {
                "user_message": {
                    "id": f"guest-{message_id}",
                    "conversation_id": "guest",
                    "role": "user",
                    "content": payload.content,
                    "status": "complete",
                    "created_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
                "message_id": message_id,
                "provider": provider.name,
                "model": spec["name"],
            },
        )

        status = "complete"

        try:
            async for delta in provider.stream(
                system,
                history,
                spec["model"],
            ):
                yield _sse(
                    "delta",
                    {
                        "message_id": message_id,
                        "text": delta,
                    },
                )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            status = "error"

            yield _sse(
                "error",
                {
                    "message_id": message_id,
                    "detail": str(exc),
                },
            )

        yield _sse(
            "done",
            {
                "message_id": message_id,
                "status": status,
            },
        )

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/{conversation_id}/stream")
async def stream_chat(
    conversation_id: str,
    payload: SendMessageRequest,
    user: Dict[str, Any] = Depends(current_user),
):
    convo = await db.conversations.find_one(
        {
            "id": conversation_id,
            "user_id": user["id"],
        }
    )

    if not convo:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    spec = _resolve_model(payload.model_id, authenticated=True, user=user)

    operation = getattr(
        payload,
        "operation",
        "chat",
    )

    if operation not in {"chat", "coding", "build"}:
        operation = "chat"

    cost = operation_cost(
        spec["id"],
        operation,
    )

    credits = await _reserve_credits(
        user,
        cost,
    )

    images, doc_text, refs = await _load_attachments(
        payload.attachment_ids,
        user["id"],
    )

    if payload.from_message_id:
        anchor = await db.messages.find_one(
            {
                "id": payload.from_message_id,
                "conversation_id": conversation_id,
            }
        )

        if not anchor:
            raise HTTPException(
                status_code=404,
                detail="Message not found",
            )

        await db.messages.delete_many(
            {
                "conversation_id": conversation_id,
                "created_at": {
                    "$gte": anchor["created_at"],
                },
            }
        )

    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=payload.content,
        attachments=[
            AttachmentRef(**ref)
            for ref in refs
        ],
    )

    user_document = user_msg.model_dump()
    user_document["user_id"] = user["id"]
    await db.messages.insert_one(user_document)

    updates: Dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc)
    }

    if convo.get("title") in (
        None,
        "",
        "New chat",
        "New session",
    ):
        updates["title"] = (
            payload.content.strip()[:60]
            or "New chat"
        )

    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": updates},
    )

    docs = (
        await db.messages.find(
            {"conversation_id": conversation_id}
        )
        .sort("created_at", 1)
        .to_list(2000)
    )

    history: List[Dict[str, str]] = [
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in docs[-MAX_HISTORY:]
    ]

    if doc_text and history:
        history[-1] = {
            "role": "user",
            "content": (
                f"{doc_text}\n\n---\n\n"
                f"{history[-1]['content']}"
            ),
        }

    persona = Persona(
        **user.get("persona", {})
    )

    system = _build_system(persona)

    if operation == "coding":
        system += (
            "\n\nThe user is in CODING mode. "
            "Prioritize correct, complete, directly usable code. "
            "Explain important changes briefly."
        )

    elif operation == "build":
        system += (
            "\n\nThe user is in BUILD mode. "
            "Think like a senior full-stack engineer. "
            "When generating a project, produce a coherent file structure "
            "and complete implementation rather than isolated snippets."
        )

    if convo.get("project_id"):
        project = await db.projects.find_one(
            {
                "id": convo["project_id"],
                "user_id": user["id"],
            }
        )

        if project and project.get("instructions"):
            system += (
                f"\n\nProject '{project['name']}' instructions: "
                f"{project['instructions'].strip()}"
            )

    assistant = Message(
        conversation_id=conversation_id,
        role="assistant",
        content="",
        status="streaming",
        model_id=spec["id"],
    )

    provider = get_provider()

    async def generator() -> AsyncIterator[str]:
        buffer = ""
        status = "complete"

        yield _sse(
            "start",
            {
                "user_message": json.loads(
                    user_msg.model_dump_json()
                ),
                "message_id": assistant.id,
                "provider": provider.name,
                "model": spec["name"],
                "credits": credits,
                "operation": operation,
            },
        )

        try:
            async for delta in provider.stream(
                system,
                history,
                spec["model"],
                images,
            ):
                buffer += delta

                yield _sse(
                    "delta",
                    {
                        "message_id": assistant.id,
                        "text": delta,
                    },
                )

        except asyncio.CancelledError:
            status = "stopped"
            raise

        except Exception as exc:
            status = "error"

            yield _sse(
                "error",
                {
                    "message_id": assistant.id,
                    "detail": str(exc),
                },
            )

        finally:
            assistant.content = buffer
            assistant.status = status

            assistant_document = assistant.model_dump()
            assistant_document["user_id"] = user["id"]
            await db.messages.insert_one(assistant_document)

            await db.conversations.update_one(
                {"id": conversation_id},
                {
                    "$set": {
                        "updated_at": datetime.now(
                            timezone.utc
                        )
                    }
                },
            )

        yield _sse(
            "done",
            {
                "message_id": assistant.id,
                "status": status,
                "credits": credits,
            },
        )

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
