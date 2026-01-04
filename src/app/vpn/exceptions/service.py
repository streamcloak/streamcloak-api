import json
from pathlib import Path
from typing import Dict, List

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.logger import logger
from app.core.utils import run_command
from app.vpn.exceptions.schemas import DomainExceptionEntry
from app.vpn.openvpn.service import OpenVPNService

settings = get_settings()

# Constants
SYNC_FLAG_PATH = Path("/tmp/domain_exceptions_needs_update.flag")
IPTABLES_SCRIPT = "/etc/openvpn/fetch_exception_ips.sh"


def get_domain_exceptions() -> Dict[str, bool]:
    """
    Safely reads the domain exceptions JSON file.
    """
    path = Path(settings.DOMAIN_EXCEPTION_PATH)

    if not path.exists():
        save_domain_exceptions({})
        return {}

    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Corrupt JSON in {path}, resetting file.")
        save_domain_exceptions({})
        return {}
    except Exception as e:
        logger.error(f"Error reading domain exceptions: {e}")
        # In case of permission errors or others, return empty to prevent crash
        return {}


def save_domain_exceptions(data: Dict[str, bool]) -> None:
    """
    Helper to save JSON data.
    """
    path = Path(settings.DOMAIN_EXCEPTION_PATH)
    try:
        # Improve ensuring directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save domain exceptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save configuration file."
        ) from e


def get_domain_exceptions_as_datatype() -> List[DomainExceptionEntry]:
    """
    Returns list format for frontend consumption.
    """
    data = get_domain_exceptions()
    return [DomainExceptionEntry(domain_url=key, active=value) for key, value in data.items()]


def domain_exceptions_needs_sync() -> bool:
    return SYNC_FLAG_PATH.exists()


def set_domain_exceptions_sync_flag() -> None:
    try:
        SYNC_FLAG_PATH.touch(exist_ok=True)
    except Exception as e:
        logger.error(f"Could not set sync flag: {e}")


def remove_domain_exceptions_sync_flag() -> None:
    try:
        if SYNC_FLAG_PATH.exists():
            SYNC_FLAG_PATH.unlink()
    except Exception as e:
        logger.error(f"Could not remove sync flag: {e}")


def sync_domain_exceptions() -> bool:
    """
    Synchronizes the domain exceptions by running system scripts.
    Relies on 'systemctl restart iptables' to atomically reload rules.
    """
    logger.info("Starting domain exception sync...")
    openvpn_service = OpenVPNService()

    # 1. Stop OpenVPN
    # Warning: Clients lose internet here due to Killswitch, which is intended behavior.
    openvpn_service.stop()

    try:
        # 2. Execute the shell script to resolve IPs/update lists
        # Assuming this script populates ipsets or config files needed by iptables
        code, stdout, stderr = run_command(["/usr/bin/bash", IPTABLES_SCRIPT])

        if code != 0:
            logger.error(f"Fetch exceptions script failed: {stderr}")
            raise Exception(f"Script execution failed: {stderr}")

        # 3. Reload Firewall Rules
        # Instead of Flushing (-F) and leaving system naked, we restart the service.
        # This assumes iptables.service loads rules from /etc/iptables/rules.v4 or similar.
        code_fw, _, err_fw = run_command(["/usr/bin/systemctl", "restart", "iptables.service"])

        if code_fw != 0:
            logger.error(f"Failed to restart iptables: {err_fw}")
            raise Exception("Firewall restart failed. System might be in inconsistent state.")

    except Exception as e:
        # Ensure we try to bring VPN back up even if script fails,
        # otherwise user is locked out.
        logger.error(f"Sync process failed: {e}")
        openvpn_service.start()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error syncing exceptions: {str(e)}"
        ) from e

    # 4. Start OpenVPN
    openvpn_service.start()

    # 5. Cleanup
    remove_domain_exceptions_sync_flag()
    logger.info("Domain exception sync completed successfully.")

    return True


def update_domain_exceptions(key: str, value: bool) -> None:
    """
    Updates or adds a domain exception entry.
    """
    if not key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain cannot be empty")

    try:
        data = get_domain_exceptions()
        data[key] = value
        save_domain_exceptions(data)
        set_domain_exceptions_sync_flag()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating entry: {str(e)}"
        ) from e


def delete_domain_exception(key: str) -> None:
    """
    Removes a domain exception entry.
    """
    try:
        data = get_domain_exceptions()
        if key in data:
            del data[key]
            save_domain_exceptions(data)
            set_domain_exceptions_sync_flag()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # 404 is semantically correct for "not found"
                detail=f"Entry '{key}' not found.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting entry: {str(e)}"
        ) from e
