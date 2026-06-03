from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from core.database import get_db
from models.audit_log import AuditLog
from models.user import HubUser
from schemas.audit import AuditLogOut, AuditLogPage

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditLogPage)
async def list_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    instance_id: int | None = None,
    action: str | None = None,
    result: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    q = select(AuditLog)
    if instance_id is not None:
        q = q.where(AuditLog.instance_id == instance_id)
    if action:
        q = q.where(AuditLog.action == action)
    if result:
        q = q.where(AuditLog.result == result)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items_result = await db.execute(q)
    items = items_result.scalars().all()

    return AuditLogPage(total=total, page=page, page_size=page_size, items=items)
