import psutil

from app.device.schemas import SystemResources


def get_cpu_temp() -> float:
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0
            return temp
    except FileNotFoundError:
        # Windows/Mac
        return -1.0


def get_system_status():
    memory_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(interval=None)
    disk_percent = psutil.disk_usage("/").percent
    cpu_temp = get_cpu_temp()
    return SystemResources(
        cpu_percent=cpu_percent,
        cpu_status=1 if cpu_percent < 50 else 2 if cpu_percent < 75 else 3,
        memory_percent=memory_percent,
        memory_status=1 if memory_percent < 50 else 2 if memory_percent < 75 else 3,
        disk_percent=disk_percent,
        disk_status=1 if disk_percent < 50 else 2 if disk_percent < 75 else 3,
        cpu_temperature=cpu_temp,
        cpu_temperature_status=1 if cpu_temp < 60 else 2 if cpu_temp < 75 else 3,
    )
