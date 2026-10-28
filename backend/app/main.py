from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, history, profiles, sessions, stats
from app.core.config import get_settings
from app.db import mongo


@asynccontextmanager
async def lifespan(_: FastAPI):
    mongo.connect()
    yield
    mongo.disconnect()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(profiles.router, prefix="/api")
    app.include_router(sessions.router, prefix="/api")
    app.include_router(history.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    return app


app = create_app()