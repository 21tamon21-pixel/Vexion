"""Public beta early-access signup."""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from lib import config
from lib.db import db

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


class WaitlistRequest(BaseModel):
    email: EmailStr


class WaitlistResponse(BaseModel):
    joined: bool
    position: int
    email: str
    message: str


@router.post("", response_model=WaitlistResponse)
async def join_waitlist(payload: WaitlistRequest):
    email = str(payload.email).lower().strip()
    existing = await db.waitlist.find_one({"email": email})
    if existing:
        return WaitlistResponse(
            joined=True,
            position=int(existing["position"]),
            email=email,
            message="You're already on the VEXION beta list.",
        )

    count = await db.waitlist.count_documents({})
    position = config.WAITLIST_START_NUMBER + count
    record: Dict[str, Any] = {
        "email": email,
        "position": position,
        "created_at": datetime.now(timezone.utc),
    }
    await db.waitlist.insert_one(record)
    return WaitlistResponse(
        joined=True,
        position=position,
        email=email,
        message="You're in. We'll let you know when beta access is available.",
    )