"""Endpoint de alertas por umbrales."""
from fastapi import APIRouter, Query

from app.metrics import collect_metrics
from app.schemas import AlertReport

router = APIRouter(tags=["Alertas"])


@router.get("/alerts", response_model=AlertReport)
def alerts(
        cpu: float = Query(80, ge=0, le=100),
        ram: float = Query(80, ge=0, le=100),
        disk: float = Query(90, ge=0, le=100),
):
    """Compara las métricas actuales contra umbrales configurables por URL."""
    m = collect_metrics()
    limits = {"cpu_percent": cpu, "ram_percent": ram, "disk_percent": disk}
    triggered = [
        {"metric": k, "value": m[k], "limit": v}
        for k, v in limits.items() if m[k] >= v
    ]
    return {"status": "ALERT" if triggered else "OK",
            "triggered": triggered, "metrics": m}