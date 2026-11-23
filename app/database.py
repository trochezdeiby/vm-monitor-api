"""Capa de acceso a datos (SQLite)."""
import sqlite3
from contextlib import closing

from app.config import DB_PATH


def get_conn() -> sqlite3.Connection:
    """Abre una conexión; las filas se leen como diccionarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Crea la tabla si no existe (se ejecuta al iniciar el servicio)."""
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