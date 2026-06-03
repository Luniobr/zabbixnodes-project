from pydantic import BaseModel


class InstanceStatus(BaseModel):
    id: int
    name: str
    url: str
    zabbix_version: str | None
    status: str
    is_active: bool
    total_hosts: int | None = None
    hosts_in_problem: int | None = None
    latency_ms: float | None = None
    error: str | None = None
    group_name: str | None = None


class DashboardResponse(BaseModel):
    total_instances: int
    healthy: int
    degraded: int
    offline: int
    instances: list[InstanceStatus]
