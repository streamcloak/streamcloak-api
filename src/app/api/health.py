from fastapi import APIRouter

from app.core.logger import logger

router = APIRouter()


@router.get("/health")
def health_check():
    logger.debug("Health check requested")
    return {"status": "ok"}
