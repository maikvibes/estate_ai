import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.database import close_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Mongo on startup so first request is fast.
    await init_db()
    try:
        yield
    finally:
        await close_db()


def create_app() -> FastAPI:
    app = FastAPI(title="Estate AI", lifespan=lifespan)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
