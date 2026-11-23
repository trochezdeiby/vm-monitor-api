"""Capa de acceso a datos (SQLite)."""
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

from app.config import DB_PATH


def get_conn() -> sqlite3.Connection:
    """Abre una conexión; las filas se leen como diccionarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea la tabla y el índice si no existen (se ejecuta al iniciar)."""
    with closing(get_conn()) as conn:
        with conn:  # commit automático
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
            # El índice acelera las consultas por rango de fechas
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_created_at "
                "ON snapshots (created_at)"
            )


def save_snapshot(m: dict, source: str) -> int:
    """Inserta una medición y devuelve su id."""
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute(
                "INSERT INTO snapshots (created_at, source, cpu_percent, "
                "ram_percent, disk_percent) VALUES (?, ?, ?, ?, ?)",
                (m["timestamp"], source, m["cpu_percent"],
                 m["ram_percent"], m["disk_percent"]),
            )
            return cur.lastrowid


def purge_old(days: int) -> int:
    """Borra las mediciones más antiguas que 'days' días. Devuelve cuántas."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(
        timespec="seconds"
    )
    with closing(get_conn()) as conn:
        with conn:
            cur = conn.execute(
                "DELETE FROM snapshots WHERE created_at < ?", (cutoff,)
            )
            return cur.rowcount