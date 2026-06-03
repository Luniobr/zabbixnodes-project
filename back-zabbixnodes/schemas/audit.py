from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    username: str | None
    action: str
    instance_name: str | None
    object_type: str | None
    object_name: str | None
    result: str | None
    error_msg: str | None
    ip_address: str | None
    created_at: datetime
    payload: Any = None

    model_config = {"from_attributes": True}


class AuditLogPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AuditLogOut]
