import asyncio
import sqlite3
import socket
import platform
import time
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from pathlib import Path

import psutil
from fastapi import FastAPI, HTTPException, Query

DB_PATH = Path(__file__).parent / "monitor.db"
AUTO_INTERVAL_SECONDS = 60  # cada cuánto se guarda un snapshot automático


# ───────────────────────── Capa de base de datos ─────────────────────────
def get_conn() -> sqlite3.Connection:
    """Abre una conexión a SQLite; las filas se pueden leer como diccionarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea la tabla si no existe (se ejecuta al iniciar el servicio)."""
    with closing(get_conn()) as conn:
        with conn:  # hace commit automático
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS snapshots (
                                                                  id           INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                  created_at   TEXT NOT NULL,
                                                                  source       TEXT NOT NULL,   -- 'manual' o 'auto'
                                                                  cpu_percent  REAL NOT NULL,
                                                                  ram_percent  REAL NOT NULL,
                                                                  disk_percent REAL NOT NULL
                         )
                         """)


def save_snapshot(m: dict, source: str) -> int:
    """Inserta una medición en la base de datos y devuelve su id."""
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute(
                "INSERT INTO snapshots (created_at, source, cpu_percent, "
                "ram_percent, disk_percent) VALUES (?, ?, ?, ?, ?)",
                (m["timestamp"], source, m["cpu_percent"],
                 m["ram_percent"], m["disk_percent"]),
            )
            return cur.lastrowid


# ───────────────────────── Lectura de métricas ─────────────────────────
def collect_metrics() -> dict:
    """Consulta al sistema operativo el estado actual del servidor."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ───────────────── Tarea en segundo plano (registro automático) ─────────────────
async def auto_recorder() -> None:
    """Guarda una medición cada AUTO_INTERVAL_SECONDS mientras el servicio vive."""
    while True:
        await asyncio.sleep(AUTO_INTERVAL_SECONDS)
        # to_thread evita bloquear el servidor mientras se mide la CPU
        await asyncio.to_thread(lambda: save_snapshot(collect_metrics(), "auto"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                                    # al arrancar
    task = asyncio.create_task(auto_recorder())
    yield
    task.cancel()                                # al apagar


app = FastAPI(
    title="VM-Monitor API",
    description="Monitoreo de recursos de un servidor Linux Mint en VirtualBox",
    version="1.0.0",
    lifespan=lifespan,
)


# ───────────────────────────── Endpoints ─────────────────────────────
@app.get("/health")
def health():
    """Comprobación rápida de que el servicio está vivo."""
    return {"status": "ok"}


@app.get("/system/info")
def system_info():
    """Información estática del servidor."""
    return {
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu_cores": psutil.cpu_count(),
        "ram_total_mb": round(psutil.virtual_memory().total / 1024**2),
    }


@app.get("/metrics")
def current_metrics():
    """Métricas en tiempo real (no se guardan)."""
    return collect_metrics()


@app.post("/snapshots", status_code=201)
def create_snapshot():
    """Mide ahora mismo y guarda el resultado en el historial."""
    m = collect_metrics()
    return {"id": save_snapshot(m, "manual"), **m}


@app.get("/snapshots")
def list_snapshots(limit: int = Query(10, ge=1, le=100)):
    """Lista las últimas mediciones guardadas (más recientes primero)."""
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/snapshots/{snapshot_id}")
def get_snapshot(snapshot_id: int):
    """Devuelve una medición específica."""
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    return dict(row)


@app.delete("/snapshots/{snapshot_id}", status_code=204)
def delete_snapshot(snapshot_id: int):
    """Elimina una medición del historial."""
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")


@app.get("/alerts")
def alerts(
        cpu: float = Query(80, ge=0, le=100),
        ram: float = Query(80, ge=0, le=100),
        disk: float = Query(90, ge=0, le=100),
):
    """Compara las métricas actuales contra umbrales (configurables por URL)."""
    m = collect_metrics()
    limits = {"cpu_percent": cpu, "ram_percent": ram, "disk_percent": disk}
    triggered = [
        {"metric": k, "value": m[k], "limit": v}
        for k, v in limits.items() if m[k] >= v
    ]
    return {"status": "ALERT" if triggered else "OK",
            "triggered": triggered, "metrics": m}