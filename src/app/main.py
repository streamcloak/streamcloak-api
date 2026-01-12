import fcntl
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.api_v1 import api_router as api_v1_router
from app.core.config import get_settings
from app.core.logger import setup_logging
from app.pihole.service import update_gravity
from app.vpn.providers.tasks import update_vpn_servers

setup_logging()

settings = get_settings()
scheduler = AsyncIOScheduler()

LOCK_FILE = "/tmp/streamcloak_scheduler.lock"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from app.core.logger import logger

    # Process-wide lock
    lock_file = open(LOCK_FILE, "w")
    try:
        # Try to get an exclusive lock (non-blocking)
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

        logger.info("🚀  StreamCloak VPN Box API is starting up...")
        import asyncio

        asyncio.create_task(update_vpn_servers())
        asyncio.create_task(update_gravity())

        scheduler.add_job(
            update_vpn_servers, trigger=IntervalTrigger(weeks=1), id="update_vpn_list", replace_existing=True
        )
        scheduler.add_job(update_gravity, trigger=IntervalTrigger(weeks=1), id="update_gravity", replace_existing=True)
        scheduler.start()

    except BlockingIOError:
        logger.info("⚡ Worker skipping scheduler (already running in another process)")

    yield

    # Cleanup
    try:
        scheduler.shutdown()
        lock_file.close()
    except:
        pass
    logger.info("🛑  StreamCloak VPN Box API is shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"

# Mounts config/static to /static URL
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(api_v1_router, prefix=settings.API_V1_STR)
