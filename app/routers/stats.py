"""Estadísticas calculadas sobre el historial de mediciones."""
from contextlib import closing
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from app.database import get_conn
from app.schemas import MetricStats, StatsReport

router = APIRouter(tags=["Estadísticas"])


def _metric(row, name: str) -> MetricStats:
    """Arma el resumen de una métrica a partir de la fila de SQL."""
    if row["samples"] == 0:
        return MetricStats(avg=None, max=None, min=None)
    return MetricStats(
        avg=round(row[f"avg_{name}"], 1),
        max=row[f"max_{name}"],
        min=row[f"min_{name}"],
    )


@router.get("/stats", response_model=StatsReport)
def stats(hours: int = Query(24, ge=1, le=720)):
    """Promedio, máximo y mínimo de las mediciones de las últimas N horas."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(
        timespec="seconds"
    )
    with closing(get_conn()) as conn:
        row = conn.execute("""
                           SELECT COUNT(*) AS samples,
                                  AVG(cpu_percent)  AS avg_cpu,  MAX(cpu_percent)  AS max_cpu,
                                  MIN(cpu_percent)  AS min_cpu,
                                  AVG(ram_percent)  AS avg_ram,  MAX(ram_percent)  AS max_ram,
                                  MIN(ram_percent)  AS min_ram,
                                  AVG(disk_percent) AS avg_disk, MAX(disk_percent) AS max_disk,
                                  MIN(disk_percent) AS min_disk
                           FROM snapshots WHERE created_at >= ?
                           """, (cutoff,)).fetchone()
    return StatsReport(
        hours=hours,
        samples=row["samples"],
        cpu=_metric(row, "cpu"),
        ram=_metric(row, "ram"),
        disk=_metric(row, "disk"),
    )