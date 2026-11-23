"""Configuración central del servicio."""
import os
from pathlib import Path

# Raíz del proyecto (una carpeta arriba de /app)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "monitor.db"

# Cada cuántos segundos se guarda una medición automática
AUTO_INTERVAL_SECONDS = 60

# La clave se lee de una variable de entorno, nunca se escribe en el código
API_KEY = os.getenv("VM_MONITOR_API_KEY", "")

# Días que se conservan las mediciones antes de borrarlas automáticamente
RETENTION_DAYS = int(os.getenv("VM_MONITOR_RETENTION_DAYS", "7"))