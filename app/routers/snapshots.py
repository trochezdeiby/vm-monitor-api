"""Endpoints del historial de mediciones."""
from contextlib import closing

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_conn, save_snapshot
from app.metrics import collect_metrics
from app.schemas import Snapshot, SnapshotCreated
from app.security import require_api_key

router = APIRouter(prefix="/snapshots", tags=["Historial"])


@router.post("", status_code=201, response_model=SnapshotCreated,
             dependencies=[Depends(require_api_key)])
def create_snapshot():
    """Mide ahora y guarda en el historial. Requiere API key."""
    m = collect_metrics()
    return {"id": save_snapshot(m, "manual"), **m}


@router.get("", response_model=list[Snapshot])
def list_snapshots(limit: int = Query(10, ge=1, le=100)):
    """Últimas mediciones guardadas (más recientes primero)."""
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{snapshot_id}", response_model=Snapshot)
def get_snapshot(snapshot_id: int):
    """Una medición específica."""
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    return dict(row)


@router.delete("/{snapshot_id}", status_code=204,
               dependencies=[Depends(require_api_key)])
def delete_snapshot(snapshot_id: int):
    """Elimina una medición. Requiere API key."""
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")