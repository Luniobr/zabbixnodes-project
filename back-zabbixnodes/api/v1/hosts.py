from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_instance_access, get_client_ip, get_current_user
from core.database import get_db
from models.instance import Instance
from models.user import HubUser
from schemas.host import HostCreate, HostOut, HostUpdate
from services import audit as audit_svc
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/instances/{instance_id}/hosts", tags=["hosts"])


async def _get_active_instance(instance_id: int, db: AsyncSession) -> Instance:
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.is_active == True)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada ou inativa")
    return instance


@router.get("")
async def list_hosts(
    instance_id: int,
    group_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    hosts = await zabbix_svc.list_hosts(instance.url, instance.api_token, group_id=group_id)
    return hosts


@router.post("", status_code=201)
async def create_host(
    instance_id: int,
    body: HostCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)

    data = body.model_dump()
    data["interfaces"] = [iface.model_dump() for iface in body.interfaces]

    try:
        result = await zabbix_svc.create_host(instance.url, instance.api_token, data)
        host_id = result["hostids"][0]
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="CREATE_HOST",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host",
            object_id=host_id,
            object_name=body.host,
            payload={"host": body.host},
            result="success",
            ip_address=get_client_ip(request),
        )
        return {"hostid": host_id, "host": body.host}
    except Exception as e:
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="CREATE_HOST",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host",
            object_name=body.host,
            result="error",
            error_msg=str(e),
            ip_address=get_client_ip(request),
        )
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{host_id}")
async def update_host(
    instance_id: int,
    host_id: str,
    body: HostUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    data = body.model_dump(exclude_none=True)
    try:
        result = await zabbix_svc.update_host(instance.url, instance.api_token, host_id, data)
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="UPDATE_HOST",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host",
            object_id=host_id,
            object_name=body.host,
            result="success",
            ip_address=get_client_ip(request),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{host_id}", status_code=204)
async def delete_host(
    instance_id: int,
    host_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        await zabbix_svc.delete_host(instance.url, instance.api_token, host_id)
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="DELETE_HOST",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host",
            object_id=host_id,
            result="success",
            ip_address=get_client_ip(request),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.patch("/{host_id}/toggle")
async def toggle_host(
    instance_id: int,
    host_id: str,
    enable: bool,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        result = await zabbix_svc.toggle_host(instance.url, instance.api_token, host_id, enable)
        action = "ENABLE_HOST" if enable else "DISABLE_HOST"
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action=action,
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host",
            object_id=host_id,
            result="success",
            ip_address=get_client_ip(request),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/groups")
async def list_host_groups(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_host_groups(instance.url, instance.api_token)


@router.get("/templates")
async def list_templates(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_templates(instance.url, instance.api_token)
