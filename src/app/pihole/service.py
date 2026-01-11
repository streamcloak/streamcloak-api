import asyncio

from app.core.config import get_settings
from app.core.logger import logger
from app.core.utils import run_command

settings = get_settings()


async def update_gravity() -> dict:
    """
    Executes 'pihole -g' to update adlists.
    Runs in a separate thread to avoid blocking the asyncio event loop.
    """

    if settings.ENVIRONMENT == "dev":
        logger.debug("Do not update gravity in dev mode...")
        return {}

    loop = asyncio.get_running_loop()

    # Since pihole -g is IO/CPU heavy and long-running, we offload it.
    try:
        # Running 'pihole -g'
        output = await loop.run_in_executor(None, run_command, ["sudo", "pihole", "-g"])

        logger.info("Pi-hole gravity updated successfully via CLI.")

        return {
            "success": True,
            "output": output,  # Contains the log output from the command
        }
    except Exception as e:
        logger.error(f"Failed to update gravity: {str(e)}")
        return {"success": False, "error": str(e)}
