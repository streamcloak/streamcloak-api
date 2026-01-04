from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.api_v1 import api_router as api_v1_router
from app.core.config import get_settings
from app.core.logger import setup_logging
from app.vpn.services import update_vpn_servers

setup_logging()

settings = get_settings()
scheduler = AsyncIOScheduler()

description = """
This API is designed to work seamlessly with **FlutterFlow**.

### ⚠️ Note on HTTP Methods
To ensure this project can be forked and used **without requiring a paid FlutterFlow subscription**, this API
creates an intentional restriction:
* It strictly uses `GET` and `POST` requests only.
* Standard `PUT`, `PATCH`, or `DELETE` methods are mapped to `POST` actions where necessary.
"""


@asynccontextmanager
async def lifespan(_app: FastAPI):
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
    description=description,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"

# Mounts config/static to /static URL
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(api_v1_router, prefix=settings.API_V1_STR)
