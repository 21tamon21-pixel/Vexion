from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from lib.db import db
from lib.security import (
    optional_user,
)
from models.schemas import Persona, PersonaUpdate, User

router = APIRouter(prefix="/profile", tags=["profile"])


def _public(doc: Dict[str, Any]) -> User:
    """Return only fields that are safe for the browser."""
    return User(
        **{
            key: value
            for key, value in doc.items()
            if key not in ("_id", "password_hash")
        }
    )


@router.get("/me", response_model=User)
async def me(
    user: Dict[str, Any] = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=400, detail="Anonymous client ID is required")
    return _public(user)


@router.patch("/persona", response_model=User)
async def update_persona(
    payload: PersonaUpdate,
    user: Dict[str, Any] = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    persona = Persona(**user.get("persona", {}))

    updates = payload.model_dump(exclude_none=True)
    persona = persona.model_copy(update=updates)

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"persona": persona.model_dump()}},
    )

    doc = await db.users.find_one({"id": user["id"]})

    if not doc:
        raise HTTPException(status_code=404, detail="User not found")

    return _public(doc)
