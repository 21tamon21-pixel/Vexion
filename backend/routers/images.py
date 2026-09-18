"""Image generation endpoint with an explicit unavailable state."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from lib.security import optional_user
from lib import config

router = APIRouter(prefix="/images", tags=["images"])


class ImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


class ImageResponse(BaseModel):
    prompt: str
    data_url: str
    caption: str
    message_id: str | None = None


@router.post("/generate", response_model=ImageResponse)
async def generate_image(
    payload: ImageRequest,
    user: Dict[str, Any] | None = Depends(optional_user),
):
    if not config.FEATURES.get("image_generation"):
        raise HTTPException(status_code=503, detail="Image generation is not configured on the server")
    raise HTTPException(status_code=503, detail="Image generation provider is unavailable")
