"""
VM-Monitor API
Punto de entrada: arma la aplicación y lanza la tarea de registro automático.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import AUTO_INTERVAL_SECONDS, RETENTION_DAYS
from app.database import init_db, purge_old, save_snapshot
from app.metrics import collect_metrics
from app.routers import alerts, snapshots, stats, system


def record_and_purge() -> None:
    """Guarda una medición automática y borra las que superen la retención."""
    save_snapshot(collect_metrics(), "auto")
    purge_old(RETENTION_DAYS)


async def auto_recorder() -> None:
    """Ejecuta record_and_purge cada AUTO_INTERVAL_SECONDS mientras el servicio vive."""
    while True:
        await asyncio.sleep(AUTO_INTERVAL_SECONDS)
        # to_thread evita bloquear el servidor mientras se mide la CPU
        await asyncio.to_thread(record_and_purge)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                                    # al arrancar
    task = asyncio.create_task(auto_recorder())
    yield
    task.cancel()                                # al apagar


app = FastAPI(
    title="VM-Monitor API",
    description="Monitoreo de recursos de un servidor Linux Mint en VirtualBox",
    version="2.1.0",
    lifespan=lifespan,
)

app.include_router(system.router)
app.include_router(snapshots.router)
app.include_router(alerts.router)
app.include_router(stats.router)