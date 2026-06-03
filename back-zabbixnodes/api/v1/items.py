from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_instance_access, get_current_user
from core.database import get_db
from models.instance import Instance
from models.user import HubUser
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/instances/{instance_id}/hosts/{host_id}/items", tags=["items"])


async def _get_active_instance(instance_id: int, db: AsyncSession) -> Instance:
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.is_active == True)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada ou inativa")
    return instance


@router.get("")
async def list_items(
    instance_id: int,
    host_id: str,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    await check_instance_access(current_user, instance_id, db)
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_host_items(
        instance.url, instance.api_token, host_id=host_id, search=search
    )


@router.get("/{item_id}/history")
async def get_history(
    instance_id: int,
    host_id: str,
    item_id: str,
    value_type: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    await check_instance_access(current_user, instance_id, db)
    if limit > 500:
        limit = 500
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.get_item_history(
        instance.url, instance.api_token, item_id=item_id, value_type=value_type, limit=limit
    )
