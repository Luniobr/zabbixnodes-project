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

router = APIRouter(prefix="/instances/{instance_id}/templates", tags=["templates"])


class LinkTemplateBody(BaseModel):
    host_ids: list[str]


class TemplateCreate(BaseModel):
    host: str
    name: str = ""
    description: str = ""
    group_ids: list[str]
    tags: list[dict] = []


class TemplateUpdate(BaseModel):
    name: str = ""
    description: str = ""
    group_ids: list[str] = []
    tags: list[dict] = []


async def _get_active_instance(instance_id: int, db: AsyncSession) -> Instance:
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.is_active == True)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada ou inativa")
    return instance


@router.get("/groups")
async def list_template_groups(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_template_groups(instance.url, instance.api_token)


@router.get("")
async def list_templates(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    return await zabbix_svc.list_templates_with_counts(instance.url, instance.api_token)


@router.post("", status_code=201)
async def create_template(
    instance_id: int,
    body: TemplateCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    data = {
        "host": body.host,
        "name": body.name or body.host,
        "description": body.description,
        "groups": [{"groupid": gid} for gid in body.group_ids],
        "tags": body.tags,
    }
    try:
        result = await zabbix_svc.create_template(instance.url, instance.api_token, data)
        templateid = result["templateids"][0]
        await audit_svc.record(
            db, user_id=current_user.id, username=current_user.username,
            action="CREATE_TEMPLATE", instance_id=instance.id, instance_name=instance.name,
            object_type="template", object_id=templateid, object_name=body.name or body.host,
            result="success", ip_address=get_client_ip(request),
        )
        return {"templateid": templateid}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{templateid}", status_code=204)
async def update_template(
    instance_id: int,
    templateid: str,
    body: TemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    data: dict = {}
    if body.name:
        data["name"] = body.name
    if body.description is not None:
        data["description"] = body.description
    if body.group_ids:
        data["groups"] = [{"groupid": gid} for gid in body.group_ids]
    if body.tags is not None:
        data["tags"] = body.tags
    try:
        await zabbix_svc.update_template(instance.url, instance.api_token, templateid, data)
        await audit_svc.record(
            db, user_id=current_user.id, username=current_user.username,
            action="UPDATE_TEMPLATE", instance_id=instance.id, instance_name=instance.name,
            object_type="template", object_id=templateid, object_name=body.name,
            result="success", ip_address=get_client_ip(request),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{templateid}/items")
async def list_template_items(
    instance_id: int,
    templateid: str,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    try:
        return await zabbix_svc.get_template_items(instance.url, instance.api_token, templateid)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{templateid}")
async def get_template(
    instance_id: int,
    templateid: str,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    try:
        return await zabbix_svc.get_template_detail(instance.url, instance.api_token, templateid)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{templateid}/link", status_code=204)
async def link_template(
    instance_id: int,
    templateid: str,
    body: LinkTemplateBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        await zabbix_svc.link_template_to_hosts(
            instance.url, instance.api_token, templateid, body.host_ids
        )
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="LINK_TEMPLATE",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="template",
            object_id=templateid,
            payload={"host_ids": body.host_ids},
            result="success",
            ip_address=get_client_ip(request),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{templateid}/hosts/{host_id}", status_code=204)
async def unlink_template(
    instance_id: int,
    templateid: str,
    host_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        await zabbix_svc.unlink_template_from_host(
            instance.url, instance.api_token, templateid, host_id
        )
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="UNLINK_TEMPLATE",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="template",
            object_id=templateid,
            payload={"host_id": host_id},
            result="success",
            ip_address=get_client_ip(request),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{templateid}", status_code=204)
async def delete_template(
    instance_id: int,
    templateid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    instance = await _get_active_instance(instance_id, db)
    await check_instance_access(current_user, instance_id, db, require_write=True)
    try:
        await zabbix_svc.delete_template(instance.url, instance.api_token, templateid)
        await audit_svc.record(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="DELETE_TEMPLATE",
            instance_id=instance.id,
            instance_name=instance.name,
            object_type="template",
            object_id=templateid,
            result="success",
            ip_address=get_client_ip(request),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
