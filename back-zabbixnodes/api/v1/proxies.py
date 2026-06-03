from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_instance_access, get_client_ip, get_current_user
from core.database import get_db
from models.instance import Instance
from models.user import HubUser
from schemas.proxy import ProxyCreate
from services import audit as audit_svc
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/instances/{instance_id}/proxies", tags=["proxies"])


async def _get_active_instance(instance_id: int, db: AsyncSession) -> Instance:
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.is_active == True)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada ou inativa")
    return instance


@router.get("")
async def list_proxies(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_proxies(instance.url, instance.api_token)


@router.post("", status_code=201)
async def create_proxy(
    instance_id: int,
    body: ProxyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    data = body.model_dump()
    try:
        result = await zabbix_svc.create_proxy(instance.url, instance.api_token, data)
        proxy_id = result["proxyids"][0]
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="CREATE_PROXY",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="proxy",
            object_id=proxy_id,
            object_name=body.name,
            payload={"name": body.name, "operating_mode": body.operating_mode},
            result="success",
            ip_address=get_client_ip(request),
        )
        return {"proxyid": proxy_id, "name": body.name}
    except Exception as e:
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="CREATE_PROXY",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="proxy",
            object_name=body.name,
            result="error",
            error_msg=str(e),
            ip_address=get_client_ip(request),
        )
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{proxy_id}", status_code=204)
async def delete_proxy(
    instance_id: int,
    proxy_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        await zabbix_svc.delete_proxy(instance.url, instance.api_token, proxy_id)
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="DELETE_PROXY",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="proxy",
            object_id=proxy_id,
            result="success",
            ip_address=get_client_ip(request),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
