"""Endpoints de estado del sistema."""
from fastapi import APIRouter, Query

from app.metrics import (collect_metrics, load_average, network_stats,
                         system_info, top_processes)
from app.schemas import LoadAverage, Metrics, NetworkStats, ProcessInfo

router = APIRouter(tags=["Sistema"])


@router.get("/health")
def health():
    """Comprobación rápida de que el servicio está vivo."""
    return {"status": "ok"}


@router.get("/system/info")
def info():
    """Información estática del servidor."""
    return system_info()


@router.get("/metrics", response_model=Metrics)
def current_metrics():
    """Métricas en tiempo real (no se guardan)."""
    return collect_metrics()


@router.get("/system/load", response_model=LoadAverage)
def load():
    """Carga promedio del sistema (1, 5 y 15 minutos)."""
    return load_average()


@router.get("/system/network", response_model=NetworkStats)
def network():
    """Tráfico de red acumulado desde el arranque."""
    return network_stats()


@router.get("/system/processes", response_model=list[ProcessInfo])
def processes(
        limit: int = Query(5, ge=1, le=20),
        sort: str = Query("cpu", pattern="^(cpu|memory)$"),
):
    """Procesos que más consumen, ordenados por 'cpu' o 'memory'."""
    return top_processes(limit, sort)