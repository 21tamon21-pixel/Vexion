import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR.parent / ".env")

from lib.db import client, db, ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.index_task = asyncio.create_task(ensure_indexes())

    try:
        yield
    finally:
        client.close()


app = FastAPI(
    title="VEXION API",
    version="1.0.0",
    lifespan=lifespan,
)

api_router = APIRouter(prefix="/api")


class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatusCheckCreate(BaseModel):
    client_name: str


@api_router.get("/")
async def root():
    return {
        "name": "VEXION",
        "status": "online",
        "version": "1.0.0",
    }


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())

    await db.status_checks.insert_one(status_obj.model_dump())

    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)

    return [
        StatusCheck(**status_check)
        for status_check in status_checks
    ]


from lib.config import public_config

from routers.attachments import router as attachments_router
from routers.api_keys import router as api_keys_router
from routers.auth import router as auth_router
from routers.chat import router as chat_router
from routers.conversations import router as conversations_router
from routers.images import router as images_router
from routers.projects import router as projects_router
from routers.usage import router as usage_router
from routers.waitlist import router as waitlist_router


@api_router.get("/config")
async def get_config():
    return public_config()


# Core VEXION API
api_router.include_router(auth_router)
api_router.include_router(conversations_router)
api_router.include_router(projects_router)
api_router.include_router(chat_router)
api_router.include_router(images_router)
api_router.include_router(attachments_router)
api_router.include_router(api_keys_router)
api_router.include_router(usage_router)
api_router.include_router(waitlist_router)


app.include_router(api_router)


FRONTEND_DIST = ROOT_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend_app(path: str):
        if path == "" or not path.startswith("api/"):
            return FileResponse(FRONTEND_DIST / "index.html")
        raise HTTPException(status_code=404, detail="Not found")


cors_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("vexion")
