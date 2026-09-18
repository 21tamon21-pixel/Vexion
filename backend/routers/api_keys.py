"""Server-generated VEXION API keys."""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from lib.db import db
from lib.security import current_user
from services.api_keys import generate_api_key, hash_api_key

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class ApiKeyResponse(BaseModel):
    key: str


@router.post("", response_model=ApiKeyResponse)
async def create_api_key(user: Dict[str, Any] = Depends(current_user)):
    raw_key = generate_api_key()
    await db.api_keys.insert_one({
        "user_id": user["id"],
        "key_hash": hash_api_key(raw_key),
    })
    return ApiKeyResponse(key=raw_key)