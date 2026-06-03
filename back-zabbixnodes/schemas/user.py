from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    password: str
    role: str = "viewer"  # superadmin | admin | operator | viewer


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserPasswordReset(BaseModel):
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    role: str
    is_active: bool
    last_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPermissionsUpdate(BaseModel):
    permissions: list[dict]  # [{"instance_id": 1, "can_write": true}, ...]
