"""Modelos de datos: definen y validan la forma de las respuestas."""
from pydantic import BaseModel


class Metrics(BaseModel):
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    uptime_seconds: int
    timestamp: str


class SnapshotCreated(Metrics):
    id: int


class Snapshot(BaseModel):
    id: int
    created_at: str
    source: str
    cpu_percent: float
    ram_percent: float
    disk_percent: float


class Triggered(BaseModel):
    metric: str
    value: float
    limit: float


class AlertReport(BaseModel):
    status: str
    triggered: list[Triggered]
    metrics: Metrics