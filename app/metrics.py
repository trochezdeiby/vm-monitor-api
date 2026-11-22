"""Lectura de métricas del sistema operativo con psutil."""
import platform
import socket
import time
from datetime import datetime, timezone

import psutil


def collect_metrics() -> dict:
    """Estado actual del servidor."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def system_info() -> dict:
    """Información estática del servidor."""
    return {
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu_cores": psutil.cpu_count(),
        "ram_total_mb": round(psutil.virtual_memory().total / 1024**2),
    }