from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.audit_log import AuditLog


class HubUser(Base):
    __tablename__ = "hub_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=lambda: datetime.now(timezone.utc)
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")
    instance_permissions: Mapped[list["UserInstancePermission"]] = relationship(
        "UserInstancePermission", back_populates="user"
    )


class UserInstancePermission(Base):
    __tablename__ = "user_instance_permissions"

    user_id: Mapped[int] = mapped_column(ForeignKey("hub_users.id", ondelete="CASCADE"), primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("instances.id", ondelete="CASCADE"), primary_key=True)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["HubUser"] = relationship("HubUser", back_populates="instance_permissions")
