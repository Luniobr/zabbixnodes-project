from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_instance_access, get_client_ip, get_current_user
from core.database import get_db
from models.instance import Instance
from models.user import HubUser
from services import audit as audit_svc
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/instances/{instance_id}/host-groups", tags=["host-groups"])


class HostGroupCreate(BaseModel):
    name: str


class HostGroupUpdate(BaseModel):
    name: str


async def _get_active_instance(instance_id: int, db: AsyncSession) -> Instance:
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.is_active == True)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada ou inativa")
    return instance


@router.get("")
async def list_host_groups(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_host_groups(instance.url, instance.api_token)


@router.post("", status_code=201)
async def create_host_group(
    instance_id: int,
    body: HostGroupCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        result = await zabbix_svc.create_host_group(instance.url, instance.api_token, body.name)
        group_id = result["groupids"][0]
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="CREATE_HOST_GROUP",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host_group",
            object_id=group_id,
            object_name=body.name,
            payload={"name": body.name},
            result="success",
            ip_address=get_client_ip(request),
        )
        return {"groupid": group_id, "name": body.name}
    except Exception as e:
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="CREATE_HOST_GROUP",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host_group",
            object_name=body.name,
            result="error",
            error_msg=str(e),
            ip_address=get_client_ip(request),
        )
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{group_id}")
async def update_host_group(
    instance_id: int,
    group_id: str,
    body: HostGroupUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        result = await zabbix_svc.update_host_group(instance.url, instance.api_token, group_id, body.name)
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="UPDATE_HOST_GROUP",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host_group",
            object_id=group_id,
            object_name=body.name,
            result="success",
            ip_address=get_client_ip(request),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{group_id}", status_code=204)
async def delete_host_group(
    instance_id: int,
    group_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        await zabbix_svc.delete_host_group(instance.url, instance.api_token, group_id)
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="DELETE_HOST_GROUP",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="host_group",
            object_id=group_id,
            result="success",
            ip_address=get_client_ip(request),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
