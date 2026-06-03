from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_client_ip, get_current_user, require_superadmin
from core.database import get_db
from core.security import encrypt_token
from models.instance import Instance
from models.instance_group import InstanceGroup
from models.user import HubUser, UserInstancePermission
from schemas.instance import (
    InstanceCreate,
    InstanceGroupCreate,
    InstanceGroupOut,
    InstanceOut,
    InstanceTestResult,
    InstanceUpdate,
)
from services import audit as audit_svc
from services.zabbix import test_connection

router = APIRouter(prefix="/instances", tags=["instances"])


class TestCredentialsRequest(BaseModel):
    url: str
    api_token: str | None = None
    api_user: str | None = None
    api_password: str | None = None

    @model_validator(mode="after")
    def validate_auth(self):
        import json
        has_token = bool(self.api_token)
        has_creds = bool(self.api_user and self.api_password)
        if not has_token and not has_creds:
            raise ValueError("Forneça token ou usuário+senha")
        return self

    def auth_bundle_str(self) -> str:
        import json
        if self.api_user and self.api_password:
            return json.dumps({"type": "credentials", "user": self.api_user, "password": self.api_password})
        return json.dumps({"type": "token", "token": self.api_token})


@router.post("/test-credentials", response_model=InstanceTestResult)
async def test_credentials(
    body: TestCredentialsRequest,
    _: HubUser = Depends(get_current_user),
):
    enc = encrypt_token(body.auth_bundle_str())
    conn = await test_connection(body.url.rstrip("/"), enc)
    return InstanceTestResult(**conn)


def _instance_query():
    return select(Instance).options(selectinload(Instance.group))


@router.get("", response_model=list[InstanceOut])
async def list_instances(
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    if current_user.role == "superadmin":
        result = await db.execute(_instance_query().order_by(Instance.name))
        instances = result.scalars().all()
        return [InstanceOut.model_validate(inst).model_copy(update={"can_write": True}) for inst in instances]

    result = await db.execute(
        select(Instance, UserInstancePermission.can_write)
        .options(selectinload(Instance.group))
        .join(UserInstancePermission, UserInstancePermission.instance_id == Instance.id)
        .where(UserInstancePermission.user_id == current_user.id)
        .order_by(Instance.name)
    )
    rows = result.all()
    return [InstanceOut.model_validate(inst).model_copy(update={"can_write": bool(cw)}) for inst, cw in rows]


@router.post("", response_model=InstanceOut, status_code=201)
async def create_instance(
    body: InstanceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    # Validate connectivity before saving
    enc_token = encrypt_token(body.auth_bundle_str())
    conn = await test_connection(body.url, enc_token)
    if not conn["success"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Falha na conexão com a instância: {conn.get('error')}",
        )

    instance = Instance(
        name=body.name,
        url=body.url,
        api_token=enc_token,
        description=body.description,
        group_id=body.group_id,
        tags=body.tags,
        zabbix_version=conn.get("version"),
        status="online",
        last_check=datetime.now(timezone.utc),
    )
    db.add(instance)
    await db.commit()
    await db.refresh(instance)

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_INSTANCE",
        instance_id=instance.id,
        instance_name=instance.name,
        object_type="instance",
        object_name=instance.name,
        result="success",
        ip_address=get_client_ip(request),
    )

    result = await db.execute(_instance_query().where(Instance.id == instance.id))
    return result.scalar_one()


@router.get("/{instance_id}", response_model=InstanceOut)
async def get_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    result = await db.execute(_instance_query().where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    return instance


@router.put("/{instance_id}", response_model=InstanceOut)
async def update_instance(
    instance_id: int,
    body: InstanceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    result = await db.execute(_instance_query().where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")

    bundle = body.auth_bundle_str()
    if bundle:
        instance.api_token = encrypt_token(bundle)

    for field, value in body.model_dump(exclude_none=True, exclude={"api_token", "api_user", "api_password"}).items():
        setattr(instance, field, value)

    instance.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_INSTANCE",
        instance_id=instance.id,
        instance_name=instance.name,
        object_type="instance",
        object_name=instance.name,
        result="success",
        ip_address=get_client_ip(request),
    )

    result = await db.execute(_instance_query().where(Instance.id == instance_id))
    return result.scalar_one()


@router.delete("/{instance_id}", status_code=204)
async def delete_instance(
    instance_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")

    name = instance.name
    await db.delete(instance)
    await db.commit()

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE_INSTANCE",
        instance_name=name,
        object_type="instance",
        object_name=name,
        result="success",
        ip_address=get_client_ip(request),
    )


@router.post("/{instance_id}/test", response_model=InstanceTestResult)
async def test_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")

    conn = await test_connection(instance.url, instance.api_token)
    instance.last_check = datetime.now(timezone.utc)
    instance.zabbix_version = conn.get("version") or instance.zabbix_version
    instance.status = "online" if conn["success"] else "offline"
    await db.commit()

    return InstanceTestResult(**conn)


@router.patch("/{instance_id}/toggle", response_model=InstanceOut)
async def toggle_instance(
    instance_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    result = await db.execute(_instance_query().where(Instance.id == instance_id))
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")

    instance.is_active = not instance.is_active
    instance.updated_at = datetime.now(timezone.utc)
    await db.commit()

    action = "ENABLE_INSTANCE" if instance.is_active else "DISABLE_INSTANCE"
    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        instance_id=instance.id,
        instance_name=instance.name,
        object_type="instance",
        object_name=instance.name,
        result="success",
        ip_address=get_client_ip(request),
    )

    result = await db.execute(_instance_query().where(Instance.id == instance_id))
    return result.scalar_one()


# Instance Groups

groups_router = APIRouter(prefix="/instance-groups", tags=["instance-groups"])


@groups_router.get("", response_model=list[InstanceGroupOut])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    result = await db.execute(select(InstanceGroup).order_by(InstanceGroup.name))
    return result.scalars().all()


@groups_router.post("", response_model=InstanceGroupOut, status_code=201)
async def create_group(
    body: InstanceGroupCreate,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    group = InstanceGroup(**body.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@groups_router.put("/{group_id}", response_model=InstanceGroupOut)
async def update_group(
    group_id: int,
    body: InstanceGroupCreate,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    result = await db.execute(select(InstanceGroup).where(InstanceGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    for field, value in body.model_dump().items():
        setattr(group, field, value)
    await db.commit()
    await db.refresh(group)
    return group


@groups_router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    result = await db.execute(select(InstanceGroup).where(InstanceGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    await db.delete(group)
    await db.commit()
