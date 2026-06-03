from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_ip, require_superadmin
from core.database import get_db
from core.security import hash_password
from models.instance import Instance
from models.user import HubUser, UserInstancePermission
from schemas.user import UserCreate, UserOut, UserPasswordReset, UserPermissionsUpdate, UserUpdate
from services import audit as audit_svc

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(require_superadmin),
):
    result = await db.execute(select(HubUser).order_by(HubUser.username))
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    existing = await db.execute(select(HubUser).where(HubUser.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username já existe")

    user = HubUser(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE_USER",
        object_type="user",
        object_id=str(user.id),
        object_name=user.username,
        result="success",
        ip_address=get_client_ip(request),
    )
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    result = await db.execute(select(HubUser).where(HubUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_USER",
        object_type="user",
        object_id=str(user.id),
        object_name=user.username,
        result="success",
        ip_address=get_client_ip(request),
    )
    return user


@router.post("/{user_id}/reset-password", status_code=204)
async def reset_password(
    user_id: int,
    body: UserPasswordReset,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    result = await db.execute(select(HubUser).where(HubUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.password_hash = hash_password(body.password)
    await db.commit()

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="RESET_PASSWORD",
        object_type="user",
        object_id=str(user.id),
        object_name=user.username,
        result="success",
        ip_address=get_client_ip(request),
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível excluir o próprio usuário")

    result = await db.execute(select(HubUser).where(HubUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    username = user.username
    await db.delete(user)
    await db.commit()

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE_USER",
        object_type="user",
        object_name=username,
        result="success",
        ip_address=get_client_ip(request),
    )


@router.get("/{user_id}/permissions")
async def get_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(require_superadmin),
):
    result = await db.execute(
        select(UserInstancePermission, Instance.name)
        .join(Instance, Instance.id == UserInstancePermission.instance_id)
        .where(UserInstancePermission.user_id == user_id)
    )
    rows = result.all()
    return [
        {"instance_id": perm.instance_id, "instance_name": name, "can_write": perm.can_write}
        for perm, name in rows
    ]


@router.put("/{user_id}/permissions", status_code=204)
async def set_permissions(
    user_id: int,
    body: UserPermissionsUpdate,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(require_superadmin),
):
    result = await db.execute(select(HubUser).where(HubUser.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    await db.execute(delete(UserInstancePermission).where(UserInstancePermission.user_id == user_id))

    for p in body.permissions:
        db.add(UserInstancePermission(
            user_id=user_id,
            instance_id=p["instance_id"],
            can_write=p.get("can_write", True),
        ))
    await db.commit()
