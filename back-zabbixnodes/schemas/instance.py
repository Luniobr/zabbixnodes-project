from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class InstanceGroupBase(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None


class InstanceGroupCreate(InstanceGroupBase):
    pass


class InstanceGroupOut(InstanceGroupBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class InstanceBase(BaseModel):
    name: str
    url: str
    description: str | None = None
    group_id: int | None = None
    tags: list[str] = []

    @field_validator("url")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        return v.rstrip("/")


class InstanceCreate(InstanceBase):
    # Auth: either token OR user+password
    api_token: str | None = None
    api_user: str | None = None
    api_password: str | None = None

    @model_validator(mode="after")
    def validate_auth(self):
        has_token = bool(self.api_token)
        has_creds = bool(self.api_user and self.api_password)
        if not has_token and not has_creds:
            raise ValueError("Forneça um Token de API ou Usuário + Senha")
        return self

    def auth_bundle_str(self) -> str:
        """Returns JSON string to encrypt as api_token."""
        import json
        if self.api_user and self.api_password:
            return json.dumps({"type": "credentials", "user": self.api_user, "password": self.api_password})
        return json.dumps({"type": "token", "token": self.api_token})


class InstanceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    api_token: str | None = None
    api_user: str | None = None
    api_password: str | None = None
    description: str | None = None
    group_id: int | None = None
    tags: list[str] | None = None

    def auth_bundle_str(self) -> str | None:
        """Returns JSON string to encrypt, or None if no auth fields provided."""
        import json
        if self.api_user and self.api_password:
            return json.dumps({"type": "credentials", "user": self.api_user, "password": self.api_password})
        if self.api_token:
            return json.dumps({"type": "token", "token": self.api_token})
        return None


class InstanceOut(InstanceBase):
    id: int
    zabbix_version: str | None
    status: str
    is_active: bool
    last_check: datetime | None
    created_at: datetime
    updated_at: datetime
    group: InstanceGroupOut | None = None
    can_write: bool = True  # sempre True para superadmin; baseado em permissão para demais

    model_config = {"from_attributes": True}


class InstanceTestResult(BaseModel):
    success: bool
    version: str | None = None
    latency_ms: float | None = None
    error: str | None = None
