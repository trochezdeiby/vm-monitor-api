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


class LoadAverage(BaseModel):
    load_1m: float
    load_5m: float
    load_15m: float
    cpu_cores: int


class NetworkStats(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


class MetricStats(BaseModel):
    avg: float | None
    max: float | None
    min: float | None


class StatsReport(BaseModel):
    hours: int
    samples: int
    cpu: MetricStats
    ram: MetricStats
    disk: MetricStats