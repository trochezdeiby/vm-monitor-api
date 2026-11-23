"""Autenticación por API key (encabezado X-API-Key)."""
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Security(api_key_header)) -> None:
    """Dependencia: bloquea la petición si la clave falta o es incorrecta."""
    if not API_KEY:
        raise HTTPException(status_code=503,
                            detail="API key no configurada en el servidor")
    # compare_digest evita ataques de temporización al comparar claves
    if key is None or not secrets.compare_digest(key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="API key inválida o ausente")