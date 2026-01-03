from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.api.api_v1 import api_router as api_v1_router
from app.core.config import get_settings
from app.core.logger import setup_logging

setup_logging()

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.logger import logger

    logger.info("🚀  StreamCloak VPN Box API is starting up...")
    yield
    logger.info("🛑  StreamCloak VPN Box API is shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Global / Health (without Prefix)
app.include_router(health.router, tags=["Health"])

app.include_router(api_v1_router, prefix=settings.API_V1_STR)
