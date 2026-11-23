"""Lectura de métricas del sistema operativo con psutil."""
import os
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


def load_average() -> dict:
    """Carga promedio del sistema (procesos en cola) en 1, 5 y 15 minutos."""
    l1, l5, l15 = os.getloadavg()
    return {
        "load_1m": round(l1, 2),
        "load_5m": round(l5, 2),
        "load_15m": round(l15, 2),
        "cpu_cores": psutil.cpu_count(),
    }


def network_stats() -> dict:
    """Contadores de red acumulados desde el arranque."""
    n = psutil.net_io_counters()
    return {
        "bytes_sent": n.bytes_sent,
        "bytes_recv": n.bytes_recv,
        "packets_sent": n.packets_sent,
        "packets_recv": n.packets_recv,
    }


def top_processes(limit: int = 5, sort: str = "cpu") -> list[dict]:
    """Procesos que más consumen, ordenados por CPU o por memoria."""
    procs = list(psutil.process_iter(["pid", "name"]))
    # La CPU de un proceso solo se puede medir entre dos lecturas:
    # la primera la "calibra" y la segunda da el valor real.
    for p in procs:
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    time.sleep(0.5)

    result = []
    for p in procs:
        try:
            result.append({
                "pid": p.pid,
                "name": p.info["name"],
                "cpu_percent": p.cpu_percent(None),
                "memory_percent": round(p.memory_percent(), 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # el proceso terminó o no tenemos permiso

    key = "cpu_percent" if sort == "cpu" else "memory_percent"
    result.sort(key=lambda x: x[key], reverse=True)
    return result[:limit]