import os

from app.core.utils import run_command

# Constants
HOSTAPD_CONF = "/etc/hostapd/hostapd.conf"
WIFI_ENABLE_FILE = "/etc/wifi_enable"


def _write_status_file(status: str) -> None:
    """
    Helper to write 1 or 0 to the status file.
    """
    try:
        with open(WIFI_ENABLE_FILE, "w") as f:
            f.write(status)
    except IOError as e:
        # Log error in production
        print(f"Error writing wifi status file: {e}")


def get_wifi_status_file() -> bool:
    """
    Reads the persistent wifi_enable flag.
    """
    if not os.path.exists(WIFI_ENABLE_FILE):
        _write_status_file("1")
        return True

    try:
        with open(WIFI_ENABLE_FILE, "r") as f:
            content = f.read().strip()

        if content == "1":
            return True
        elif content == "0":
            return False
        else:
            _write_status_file("1")
            return True
    except IOError:
        return False


def control_hostapd(action: str) -> bool:
    """
    Controls the hostapd service via systemctl.
    Action: 'start' or 'stop'.
    """
    if action == "start":
        # Enable ensures persistence after reboot
        run_command(["/usr/bin/systemctl", "unmask", "hostapd"])  # Safety net
        run_command(["/usr/bin/systemctl", "enable", "hostapd"])
        code, _, _ = run_command(["/usr/bin/systemctl", "restart", "hostapd"])
        return code == 0

    elif action == "stop":
        run_command(["/usr/bin/systemctl", "disable", "hostapd"])
        code, _, _ = run_command(["/usr/bin/systemctl", "stop", "hostapd"])
        return code == 0

    return False


def set_wifi_state(enabled: bool) -> bool:
    """
    Updates status file and triggers systemd service.
    """
    if enabled:
        _write_status_file("1")
        return control_hostapd("start")
    else:
        _write_status_file("0")
        return control_hostapd("stop")


def read_config_value(key: str) -> str:
    """
    Parses hostapd.conf for specific keys (ssid or wpa_passphrase).
    """
    if not os.path.exists(HOSTAPD_CONF):
        return "-"

    try:
        with open(HOSTAPD_CONF, "r") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    except IOError:
        return "-"
    return "-"


def update_config_value(key: str, value: str) -> bool:
    """
    Updates a specific key in hostapd.conf safely.
    It reads all lines, modifies the target, and writes back.
    """
    if not os.path.exists(HOSTAPD_CONF):
        return False

    updated = False
    new_lines = []

    try:
        with open(HOSTAPD_CONF, "r") as f:
            lines = f.readlines()

        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                updated = True
            else:
                new_lines.append(line)

        # If key wasn't found, you might want to append it,
        # but for hostapd strict structure, better to only edit existing.
        if updated:
            with open(HOSTAPD_CONF, "w") as f:
                f.writelines(new_lines)

            # Restart service to apply changes if it's currently enabled
            if get_wifi_status_file():
                control_hostapd("start")
            return True
        return False

    except IOError:
        return False
