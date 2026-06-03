from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog


async def record(
    db: AsyncSession,
    *,
    user_id: int | None,
    username: str | None,
    action: str,
    instance_id: int | None = None,
    instance_name: str | None = None,
    object_type: str | None = None,
    object_id: str | None = None,
    object_name: str | None = None,
    payload: dict | None = None,
    result: str,
    error_msg: str | None = None,
    ip_address: str | None = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        instance_id=instance_id,
        instance_name=instance_name,
        object_type=object_type,
        object_id=object_id,
        object_name=object_name,
        payload=payload,
        result=result,
        error_msg=error_msg,
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()
