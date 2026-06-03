from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_instance_access, get_current_user
from core.database import get_db
from models.instance import Instance
from models.user import HubUser
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/instances/{instance_id}/triggers", tags=["triggers"])


async def _get_active_instance(instance_id: int, db: AsyncSession) -> Instance:
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.is_active == True)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada ou inativa")
    return instance


@router.get("")
async def list_triggers(
    instance_id: int,
    group_id: str | None = None,
    host_id: str | None = None,
    min_severity: int = 0,
    only_problems: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    await check_instance_access(current_user, instance_id, db)
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_triggers(
        instance.url,
        instance.api_token,
        only_problems=only_problems,
        group_id=group_id,
        host_id=host_id,
        min_severity=min_severity,
    )


class AckRequest(BaseModel):
    event_id: str
    message: str = ""


@router.post("/{trigger_id}/ack")
async def acknowledge(
    instance_id: int,
    trigger_id: str,
    body: AckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    await check_instance_access(current_user, instance_id, db, require_write=True)
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.acknowledge_event(
        instance.url,
        instance.api_token,
        event_id=body.event_id,
        message=body.message,
    )
