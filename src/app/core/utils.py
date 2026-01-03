import subprocess
from typing import List, Tuple

from app.core.logger import logger


def run_command(cmd: List[str], check: bool = False) -> Tuple[int, str, str]:
    cmd_str = " ".join(cmd)
    logger.info(f"Executing command: {cmd_str}")

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,  # catches stdout/stderr
            text=True,  # Returns strings instead of bytes
            check=check,  # raises CalledProcessError on error if true
        )

        if process.returncode != 0:
            logger.warning(f"Command failed ({process.returncode}): {process.stderr.strip()}")

        return process.returncode, process.stdout.strip(), process.stderr.strip()

    except FileNotFoundError:
        err_msg = f"Command not found: {cmd[0]}"
        logger.error(err_msg)
        # Return code 127 ist Standard für "Command not found"
        return 127, "", err_msg

    except Exception as e:
        logger.error(f"Unexpected error executing {cmd_str}: {e}")
        return -1, "", str(e)
