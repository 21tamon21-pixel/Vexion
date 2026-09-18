"""Anonymous client identity for the beta API."""
from __future__ import annotations

import uuid
import re
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException

from lib.db import db
from models.schemas import Persona, User

ANONYMOUS_HEADER = "X-Vexion-Client-ID"
_CLIENT_ID = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


async def _anonymous_user(client_id: Optional[str]) -> Dict[str, Any]:
    if not client_id or not _CLIENT_ID.fullmatch(client_id):
        raise HTTPException(status_code=400, detail="A valid anonymous client ID is required")

    user_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"vexion:{client_id}"))
    existing = await db.users.find_one({"id": user_id})
    if existing:
        return existing

    user = User(
        id=user_id,
        email=f"{user_id}@anonymous.vexion.local",
        name="Guest",
        persona=Persona(),
    )
    document = user.model_dump()
    document["anonymous_client_id"] = client_id
    document["anonymous"] = True
    await db.users.insert_one(document)
    return document


async def current_user(
    client_id: Optional[str] = Header(default=None, alias=ANONYMOUS_HEADER),
) -> Dict[str, Any]:
    return await _anonymous_user(client_id)


async def optional_user(
    client_id: Optional[str] = Header(default=None, alias=ANONYMOUS_HEADER),
):
    return await _anonymous_user(client_id)
