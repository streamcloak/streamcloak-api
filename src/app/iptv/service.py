import glob
import os
import re
import shlex
import socket
import subprocess
from pathlib import Path

from fastapi import HTTPException

from app.core.logger import logger
from app.core.utils import run_command
from app.iptv.schemas import IPTVProxyCreate, IPTVProxyResponse, ServiceOperationResponse, ServiceStatus

SERVICE_DIR = "/etc/systemd/system"
SCRIPT_DIR = "/usr/local/bin"
PORT_RANGE = range(9000, 9999 + 1)
M3U_CACHE_EXPIRATION = 6  # in hours - CAUTION: Do not change unless you also change /usr/bin/local/cleanup_iptv_tmp.sh


def _get_next_free_port() -> int:
    """
    Finds the next free port in the PORT_RANGE.
    """
    existing_ports = set()
    files = glob.glob(os.path.join(SERVICE_DIR, "iptv-proxy-*.service"))

    for f in files:
        match = re.search(r"iptv-proxy-(\d+)\.service", f)
        if match:
            existing_ports.add(int(match.group(1)))

    for port in PORT_RANGE:
        if port not in existing_ports:
            return port

    raise ResourceWarning(f"No free ports available in the range {PORT_RANGE[0]}-{PORT_RANGE[-1]}!")


def _get_description_from_unit(service_path: str) -> str:
    """
    Reads the description directly from the service file.
    """
    try:
        with open(service_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("Description="):
                    return line.strip().split("=", 1)[1]
    except Exception as e:
        logger.warning(f"Cannot open service file from {service_path}: {e}")
        pass
    return "Unknown service"


def _is_port_open(port: int) -> bool:
    """
    Checks whether the port accepts TCP connections.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.warning(f"Cannot check port {port} status: {e}")
        return False


def _parse_script_content(filepath: str) -> dict | None:
    """
    Reads the shell script and extracts the arguments via regex.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
        tokens = shlex.split(content)

        data = {}

        # Mapping from CLI-Parametern to internal keys
        key_map = {
            "--m3u-url": "m3u_url",
            "--hostname": "hostname",
            "--user": "user",
            "--password": "password",
            "--xtream-user": "xtream_user",
            "--xtream-password": "xtream_password",
            "--xtream-base-url": "xtream_base_url",
        }

        iterator = iter(tokens)
        for token in iterator:
            if token in key_map:
                try:
                    value = next(iterator)

                    data[key_map[token]] = value
                except StopIteration:
                    pass
        print(data)
        return data
    except Exception as e:
        logger.error(f"Error parsing {filepath}: {str(e)}")
        return None


def _write_service_files(port: int, data: IPTVProxyCreate) -> str:
    """
    Creates .sh and .service files physically on the disk.
    """
    if "\n" in data.name or "\r" in data.name:
        raise ValueError("Security breach: Name contains newlines.")

    service_name = f"iptv-proxy-{port}.service"
    script_name = f"iptv-proxy-{port}.sh"
    script_path = os.path.join(SCRIPT_DIR, script_name)
    service_path = os.path.join(SERVICE_DIR, service_name)

    base_cmd = ["/usr/bin/iptv-proxy"]
    cmd_args_list = []

    if data.xtream_user and data.xtream_password and data.xtream_base_url:
        full_m3u_url = (
            f"{data.xtream_base_url}/get.php?"
            f"username={data.xtream_user}&"
            f"password={data.xtream_password}&"
            f"type=m3u_plus&"
            f"output=m3u8"
        )

        cmd_args_list.append(("--m3u-url", full_m3u_url))
        cmd_args_list.append(("--port", str(port)))
        cmd_args_list.append(("--hostname", data.hostname))
        cmd_args_list.append(("--xtream-user", data.xtream_user))
        cmd_args_list.append(("--xtream-password", data.xtream_password))
        cmd_args_list.append(("--xtream-base-url", data.xtream_base_url))
        cmd_args_list.append(("--user", data.user))
        cmd_args_list.append(("--password", data.password))
        cmd_args_list.append(("--m3u-cache-expiration", M3U_CACHE_EXPIRATION))
    else:
        # Default
        if not data.m3u_url:
            raise ValueError("m3u URL is missing")

        cmd_args_list.append(("--m3u-url", data.m3u_url))
        cmd_args_list.append(("--port", str(port)))
        cmd_args_list.append(("--hostname", data.hostname))
        cmd_args_list.append(("--user", data.user))
        cmd_args_list.append(("--password", data.password))
        cmd_args_list.append(("--m3u-cache-expiration", M3U_CACHE_EXPIRATION))

    for flag, value in cmd_args_list:
        # shlex.quote() ensures security and correct quotation marks.
        # It automatically escapes spaces, special characters, etc.
        safe_value = shlex.quote(str(value))

        # Add line: e.g., "   --port 9001"
        base_cmd.append(f"  {flag} {safe_value}")
    full_command = " \\\n".join(base_cmd)

    script_content = f"#!/bin/bash\n\n# Auto-generated by FastAPI Controller\n{full_command}\n"

    unit_content = (
        "[Unit]\n"
        f"Description={data.name}\n"
        "After=network.target openvpn@client.service\n"
        "Requires=openvpn@client.service\n\n"
        "[Service]\n"
        "User=iptvproxy\n"
        "Group=iptvproxy\n"
        f"ExecStart={script_path}\n"
        "StandardOutput=null\n"
        "StandardError=null\n"
        "Restart=always\n"
        "RestartSec=20\n"
        "BindReadOnlyPaths=/etc/resolv.iptv-proxy.conf:/etc/resolv.conf\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )

    try:
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        with open(service_path, "w") as f:
            f.write(unit_content)

    except OSError as e:
        # Cleanup
        if os.path.exists(script_path):
            os.remove(script_path)
        if os.path.exists(service_path):
            os.remove(service_path)
        raise RuntimeError(f"Error writing service file: {e}") from e

    return service_name


def _get_service_data(port: int) -> IPTVProxyResponse | None:
    """
    Central logic: Collects all information for a specific port.
    Returns None if the files are missing or corrupt.
    """
    service_name = f"iptv-proxy-{port}.service"
    script_name = f"iptv-proxy-{port}.sh"

    service_path = os.path.join(SERVICE_DIR, service_name)
    script_path = os.path.join(SCRIPT_DIR, script_name)

    if not os.path.exists(service_path) or not os.path.exists(script_path):
        return None

    try:
        config = _parse_script_content(script_path)
        service_name_ui = _get_description_from_unit(service_path)

        hostname = config.get("hostname")

        if config.get("xtream_base_url"):
            mode = "xtream"
            proxy_url = f"http://{hostname}:{port}"
        else:
            mode = "m3u"
            user = config.get("user", "")
            pw = config.get("password", "")
            proxy_url = f"http://{hostname}:{port}/iptv.m3u?username={user}&password={pw}"

        is_active = False
        is_enabled = False
        try:
            run_command(["systemctl", "is-active", "--quiet", service_name], check=True)
            is_active = True
        except subprocess.CalledProcessError:
            pass

        try:
            run_command(["systemctl", "is-enabled", "--quiet", service_name], check=True)
            is_enabled = True
        except subprocess.CalledProcessError:
            pass

        status_detail = ServiceStatus.STOPPED
        if is_active:
            if _is_port_open(port):
                status_detail = ServiceStatus.RUNNING
            else:
                status_detail = ServiceStatus.STARTING
        else:
            _, stdout, _ = run_command(["systemctl", "show", "-p", "ActiveState", service_name])
            if "failed" in stdout:
                status_detail = ServiceStatus.FAILED

        context = {
            "id": port,
            "port": port,
            "mode": mode,
            "name": service_name_ui,
            "filename": service_name,
            "active": is_active,
            "enabled": is_enabled,
            "status_detail": status_detail,
            "proxy_url": proxy_url,
            **config,  # spread operator for m3u_url, xtream settings etc.
        }
        return IPTVProxyResponse.model_validate(context)

    except Exception as e:
        logger.error(f"Error reading from port {port}: {e}")
        return None


def get_all_services() -> list[IPTVProxyResponse]:
    """
    Reads all services directly from the system.
    """
    services = []

    files = glob.glob(os.path.join(SERVICE_DIR, "iptv-proxy-*.service"))

    for service_file in files:
        # get port from filename
        match = re.search(r"iptv-proxy-(\d+)\.service", os.path.basename(service_file))
        if not match:
            continue

        port = int(match.group(1))

        data = _get_service_data(port)

        if data:
            services.append(data)

    services.sort(key=lambda x: x.name)
    return services


def get_service(port: int) -> IPTVProxyResponse:
    """
    Reads exactly one service based on the port.
    """

    data = _get_service_data(port)

    if not data:
        raise HTTPException(status_code=404, detail=f"Proxy service on port {port} not found.")

    return data


def create_service(data: IPTVProxyCreate) -> ServiceOperationResponse:
    port = _get_next_free_port()

    try:
        service_name = _write_service_files(port, data)

        run_command(["systemctl", "daemon-reload"])
        run_command(["systemctl", "enable", service_name])
        run_command(["systemctl", "start", service_name])

        logger.info(f"Service {service_name} created.")
        context = {"service_name": service_name, "action": "create", "result": "ok", "port": port}
        return ServiceOperationResponse.model_validate(context)

    except Exception as e:
        # Simple cleanup
        script_path = os.path.join(SCRIPT_DIR, f"iptv-proxy-{port}.sh")
        service_path = os.path.join(SERVICE_DIR, f"iptv-proxy-{port}.service")
        if os.path.exists(script_path):
            os.remove(script_path)
        if os.path.exists(service_path):
            os.remove(service_path)
        raise e


def update_service(port: int, data: IPTVProxyCreate) -> ServiceOperationResponse:
    """
    Updates an existing service.
    The port remains the same, but parameters (URL, user, password) are overwritten.
    """
    service_name = f"iptv-proxy-{port}.service"
    service_path = os.path.join(SERVICE_DIR, service_name)

    if not os.path.exists(service_path):
        raise FileNotFoundError(f"Service on port {port} does not exist.")

    try:
        logger.info(f"Updating config for port {port}...")
        _write_service_files(port, data)

        # Systemd Reload & Restart
        run_command(["systemctl", "daemon-reload"])
        run_command(["systemctl", "restart", service_name])

        logger.info(f"Service {service_name} updated.")

        context = {"service_name": service_name, "action": "update", "result": "ok", "port": port}
        return ServiceOperationResponse.model_validate(context)

    except Exception as e:
        logger.error(f"Error on update from port {port}: {e}")
        raise e


def delete_service(port: int) -> ServiceOperationResponse:
    """
    Stops service, removes files, reloads daemon.
    """
    if not isinstance(port, int) or not (9000 <= port <= 9999):
        raise ValueError(f"Invalid port: {port}. Must be between 9000 and 9999.")
    port = int(port)

    service_name = f"iptv-proxy-{port}.service"
    script_name = f"iptv-proxy-{port}.sh"
    service_path = os.path.join(SERVICE_DIR, service_name)
    script_path = os.path.join(SCRIPT_DIR, script_name)

    if not os.path.exists(service_path):
        raise FileNotFoundError(f"Service {service_name} not found.")

    try:
        # Stop and disable
        try:
            run_command(["systemctl", "stop", service_name])
            run_command(["systemctl", "disable", service_name])
        except Exception as e:
            logger.warning(f"Warning while stopping {service_name} (ignored): {e}")

        # Delete files
        Path(service_path).unlink(missing_ok=True)
        Path(script_path).unlink(missing_ok=True)

        # Reload
        run_command(["systemctl", "daemon-reload"])

        logger.info(f"Service {service_name} deleted.")
        context = {"service_name": service_name, "action": "delete", "result": "ok", "port": port}
        return ServiceOperationResponse.model_validate(context)

    except Exception as e:
        logger.error(f"Error while deleting service on port {port}: {e}")
        raise RuntimeError(f"System error while deleting: {e}") from e


def restart_iptv_service(port: int) -> ServiceOperationResponse:
    service_name = f"iptv-proxy-{port}.service"
    command = ["sudo", "systemctl", "restart", service_name]

    try:
        run_command(command)
        logger.info(f"Service {service_name} restarted.")
        context = {"service_name": service_name, "action": "restart", "result": "ok", "port": port}
        return ServiceOperationResponse.model_validate(context)

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "Unknown error from systemd"
        raise RuntimeError(f"Unable to restart service: {error_msg}") from e

    except Exception as e:
        logger.error(f"General error in restart_iptv_service logic: {str(e)}")
        raise RuntimeError("An unexpected internal error has occurred.") from e
