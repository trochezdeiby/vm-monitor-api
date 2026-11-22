"""Endpoints de estado del sistema."""
from fastapi import APIRouter

from app.metrics import collect_metrics, system_info
from app.schemas import Metrics

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