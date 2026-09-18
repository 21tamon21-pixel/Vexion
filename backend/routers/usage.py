"""VEXION usage and weekly credit tracking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from lib import config
from lib.db import db
from lib.security import current_user
from models.schemas import UsageSummary

router = APIRouter(prefix="/usage", tags=["usage"])


def _week_key(now: datetime) -> str:
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _next_reset(now: datetime) -> datetime:
    days_until_monday = (7 - now.weekday()) % 7

    reset = (
        now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        + timedelta(days=days_until_monday)
    )

    if reset <= now:
        reset += timedelta(days=7)

    return reset


async def ensure_credit_state(
    user: Dict[str, Any],
) -> Dict[str, Any]:
    """Return the user's current weekly credit state.

    A new week automatically receives a fresh 10,000-credit allowance.
    """

    now = datetime.now(timezone.utc)
    current_week = _week_key(now)

    state = user.get("credits") or {}

    if state.get("week_key") == current_week:
        allowance = int(
            state.get(
                "allowance",
                config.WEEKLY_CREDIT_ALLOWANCE,
            )
        )

        used = int(state.get("used", 0))

        remaining = max(
            0,
            allowance - used,
        )

        return {
            "allowance": allowance,
            "used": used,
            "remaining": remaining,
            "reset_at": state.get(
                "reset_at",
                _next_reset(now).isoformat(),
            ),
            "week_key": current_week,
        }

    allowance = config.WEEKLY_CREDIT_ALLOWANCE
    reset_at = _next_reset(now)

    fresh = {
        "allowance": allowance,
        "used": 0,
        "remaining": allowance,
        "reset_at": reset_at,
        "week_key": current_week,
        "updated_at": now,
    }

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"credits": fresh}},
    )

    return {
        "allowance": allowance,
        "used": 0,
        "remaining": allowance,
        "reset_at": reset_at.isoformat(),
        "week_key": current_week,
    }


@router.get("", response_model=UsageSummary)
@router.get("/summary", response_model=UsageSummary)
async def usage(
    user: Dict[str, Any] = Depends(current_user),
):
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    credits = await ensure_credit_state(user)

    user_id = user["id"]

    user_messages = await db.messages.find({"user_id": user_id}).to_list(5000)
    messages = len(user_messages)

    conversations = await db.conversations.count_documents(
        {"user_id": user_id}
    )

    projects = await db.projects.count_documents(
        {"user_id": user_id}
    )

    images = await db.attachments.count_documents(
        {
            "user_id": user_id,
            "kind": "image",
        }
    )

    assistant_messages = [m for m in user_messages if m.get("role") == "assistant"]
    by_model_counts: Dict[str, int] = {"vex-ai": len(assistant_messages)}
    by_day_counts: Dict[str, int] = {}
    for message in assistant_messages:
        created = message.get("created_at")
        day = created.date().isoformat() if isinstance(created, datetime) else "unknown"
        by_day_counts[day] = by_day_counts.get(day, 0) + 1

    by_model = [
        {
            "model_id": model_id,
            "model_name": "VEX AI",
            "messages": count,
            "approx_tokens": 0,
        }
        for model_id, count in sorted(by_model_counts.items(), key=lambda item: -item[1])
    ]
    by_day = [
        {"day": day, "messages": count}
        for day, count in sorted(by_day_counts.items())
        if day != "unknown"
    ]

    return UsageSummary(
        total_messages=messages,
        total_conversations=conversations,
        total_projects=projects,
        images_generated=images,
        approx_tokens=0,
        credits_used=credits["used"],
        credits_remaining=credits["remaining"],
        credit_allowance=credits["allowance"],
        credit_reset_at=credits["reset_at"],
        by_model=by_model,
        by_day=by_day,
        quotas={
            "resets_at": credits["reset_at"],
            "limits": {"max_tier": 5},
            "ai": {"daily_used": messages, "daily_limit": config.WEEKLY_CREDIT_ALLOWANCE},
            "tavily": {"daily_used": 0, "daily_limit": 0, "monthly_used": 0, "monthly_limit": 0, "project_daily_used": 0, "project_daily_limit": 0},
        },
        storage={"used_bytes": 0, "total_bytes": 0, "files": 0, "attachment_bytes": 0, "project_bytes": 0},
        cache={"used_bytes": 0, "total_bytes": 0, "items": 0, "ttl_minutes": 0},
    )
