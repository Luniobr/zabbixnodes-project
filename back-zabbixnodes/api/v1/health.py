import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import check_instance_access, get_current_user
from core.database import get_db
from models.instance import Instance
from models.user import HubUser, UserInstancePermission
from services.health_score import calculate_health_score

router = APIRouter(tags=["health"])


async def _get_active_instance(instance_id: int, db: AsyncSession) -> Instance:
    result = await db.execute(
        select(Instance).where(Instance.id == instance_id, Instance.is_active == True)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada ou inativa")
    return instance


@router.get("/instances/{instance_id}/health")
async def get_instance_health(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    """Health Score de uma instância específica."""
    await check_instance_access(current_user, instance_id, db)
    instance = await _get_active_instance(instance_id, db)
    result = await calculate_health_score(instance.url, instance.api_token)
    return {"instance_id": instance_id, "name": instance.name, **result}


@router.get("/health")
async def get_all_health(
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    """Health Score de todas as instâncias acessíveis ao usuário."""
    query = select(Instance).options(selectinload(Instance.group)).where(Instance.is_active == True)

    if current_user.role != "superadmin":
        query = (
            query
            .join(UserInstancePermission, UserInstancePermission.instance_id == Instance.id)
            .where(UserInstancePermission.user_id == current_user.id)
        )

    result = await db.execute(query)
    instances = result.scalars().all()

    async def _score(inst: Instance) -> dict:
        data = await calculate_health_score(inst.url, inst.api_token)
        return {
            "instance_id": inst.id,
            "name": inst.name,
            "url": inst.url,
            "group_name": inst.group.name if inst.group else None,
            **data,
        }

    scores = await asyncio.gather(*[_score(i) for i in instances], return_exceptions=True)

    final = []
    for i, s in enumerate(scores):
        if isinstance(s, Exception):
            final.append({
                "instance_id": instances[i].id,
                "name": instances[i].name,
                "url": instances[i].url,
                "group_name": instances[i].group.name if instances[i].group else None,
                "score": None,
                "label": None,
                "color": None,
                "error": str(s),
                "dimensions": {},
            })
        else:
            final.append(s)

    return final
