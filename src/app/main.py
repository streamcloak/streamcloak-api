from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from app.api import health
from app.api.api_v1 import api_router as api_v1_router
from app.core.config import get_settings
from app.core.logger import setup_logging
from app.vpn.services import update_vpn_servers

setup_logging()

settings = get_settings()
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.logger import logger

    logger.info("🚀  StreamCloak VPN Box API is starting up...")
    import asyncio

    asyncio.create_task(update_vpn_servers())

    scheduler.add_job(update_vpn_servers, trigger=IntervalTrigger(weeks=1), id="update_vpn_list", replace_existing=True)
    scheduler.start()

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
