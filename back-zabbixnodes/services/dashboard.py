import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.instance import Instance
from models.user import UserInstancePermission
from schemas.dashboard import DashboardResponse, InstanceStatus
from services.zabbix import get_instance_stats


async def _fetch_instance_status(instance: Instance) -> InstanceStatus:
    if not instance.is_active:
        return InstanceStatus(
            id=instance.id,
            name=instance.name,
            url=instance.url,
            zabbix_version=instance.zabbix_version,
            status="inactive",
            is_active=False,
            group_name=instance.group.name if instance.group else None,
        )

    stats = await get_instance_stats(instance.url, instance.api_token)

    if stats["success"]:
        latency = stats["latency_ms"]
        if latency < 500:
            status = "online"
        elif latency < 2000:
            status = "slow"
        else:
            status = "slow"

        return InstanceStatus(
            id=instance.id,
            name=instance.name,
            url=instance.url,
            zabbix_version=stats.get("version"),
            status=status,
            is_active=True,
            total_hosts=stats.get("total_hosts"),
            hosts_in_problem=stats.get("hosts_in_problem"),
            latency_ms=latency,
            group_name=instance.group.name if instance.group else None,
        )
    else:
        return InstanceStatus(
            id=instance.id,
            name=instance.name,
            url=instance.url,
            zabbix_version=instance.zabbix_version,
            status="offline",
            is_active=True,
            error=stats.get("error"),
            group_name=instance.group.name if instance.group else None,
        )


async def get_dashboard(db: AsyncSession, user_id: int, is_superadmin: bool) -> DashboardResponse:
    query = select(Instance).options(selectinload(Instance.group)).where(Instance.is_active == True)
    if not is_superadmin:
        query = (
            query
            .join(UserInstancePermission, UserInstancePermission.instance_id == Instance.id)
            .where(UserInstancePermission.user_id == user_id)
        )
    result = await db.execute(query)
    instances = result.scalars().all()

    tasks = [_fetch_instance_status(inst) for inst in instances]
    statuses = await asyncio.gather(*tasks, return_exceptions=True)

    valid: list[InstanceStatus] = []
    for i, s in enumerate(statuses):
        if isinstance(s, Exception):
            inst = instances[i]
            valid.append(InstanceStatus(
                id=inst.id,
                name=inst.name,
                url=inst.url,
                zabbix_version=inst.zabbix_version,
                status="offline",
                is_active=True,
                error=str(s),
                group_name=inst.group.name if inst.group else None,
            ))
        else:
            valid.append(s)

    healthy = sum(1 for s in valid if s.status == "online")
    degraded = sum(1 for s in valid if s.status == "slow")
    offline = sum(1 for s in valid if s.status in ("offline", "auth_error"))

    return DashboardResponse(
        total_instances=len(valid),
        healthy=healthy,
        degraded=degraded,
        offline=offline,
        instances=valid,
    )
