import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_client_ip, get_current_user, require_superadmin
from core.database import get_db
from models.instance import Instance
from models.orchestration import OrchestrationResult, OrchestrationRun
from models.user import HubUser
from services import audit as audit_svc
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


class CreateHostGroupRequest(BaseModel):
    name: str
    instance_ids: list[int]


class ToggleHostsRequest(BaseModel):
    pattern: str
    enable: bool
    instance_ids: list[int]


async def _get_active_instances(db: AsyncSession, instance_ids: list[int]) -> list[Instance]:
    result = await db.execute(
        select(Instance).where(Instance.id.in_(instance_ids), Instance.is_active == True)
    )
    return result.scalars().all()


async def _save_run(
    db: AsyncSession,
    run_type: str,
    user_id: int,
    parameters: dict,
    results: list[dict],
) -> OrchestrationRun:
    run = OrchestrationRun(
        type=run_type,
        triggered_by=user_id,
        parameters=parameters,
        status="completed",
        finished_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()
    for r in results:
        db.add(OrchestrationResult(
            run_id=run.id,
            instance_id=r.get("instance_id"),
            instance_name=r.get("instance_name"),
            status=r.get("status"),
            details={k: v for k, v in r.items() if k not in ("instance_id", "instance_name", "status")},
        ))
    await db.commit()
    return run


@router.post("/create-host-group")
async def create_host_group(
    body: CreateHostGroupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    if not body.name.strip():
        raise HTTPException(status_code=422, detail="Nome do grupo é obrigatório")
    if not body.instance_ids:
        raise HTTPException(status_code=422, detail="Selecione ao menos uma instância")

    instances = await _get_active_instances(db, body.instance_ids)

    async def _run(instance: Instance) -> dict:
        try:
            result = await zabbix_svc.create_host_group(instance.url, instance.api_token, body.name)
            return {
                "instance_id": instance.id,
                "instance_name": instance.name,
                "status": "success",
                "group_id": result.get("groupids", [None])[0],
            }
        except Exception as e:
            err = str(e)
            if "already exist" in err.lower() or "duplicate" in err.lower():
                return {"instance_id": instance.id, "instance_name": instance.name, "status": "already_exists"}
            return {"instance_id": instance.id, "instance_name": instance.name, "status": "error", "error": err}

    results = list(await asyncio.gather(*[_run(inst) for inst in instances]))

    run = await _save_run(
        db,
        run_type="CREATE_HOST_GROUP",
        user_id=current_user.id,
        parameters={"group_name": body.name, "instance_ids": body.instance_ids},
        results=results,
    )

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="MASS_CREATE_HOST_GROUP",
        object_type="host_group",
        object_name=body.name,
        payload={"instances": len(instances)},
        result="success",
        ip_address=get_client_ip(request),
    )

    return {"run_id": run.id, "results": results}


@router.post("/toggle-hosts")
async def toggle_hosts(
    body: ToggleHostsRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    if not body.pattern.strip():
        raise HTTPException(status_code=422, detail="Padrão de hostname é obrigatório")
    if not body.instance_ids:
        raise HTTPException(status_code=422, detail="Selecione ao menos uma instância")

    instances = await _get_active_instances(db, body.instance_ids)

    async def _run(instance: Instance) -> dict:
        try:
            hosts = await zabbix_svc.list_hosts(instance.url, instance.api_token)
            pattern_lower = body.pattern.lower()
            matching = [
                h for h in hosts
                if pattern_lower in h.get("host", "").lower()
                or pattern_lower in h.get("name", "").lower()
            ]
            if not matching:
                return {
                    "instance_id": instance.id,
                    "instance_name": instance.name,
                    "status": "no_match",
                    "matched": 0,
                }
            toggle_tasks = [
                zabbix_svc.toggle_host(instance.url, instance.api_token, h["hostid"], body.enable)
                for h in matching
            ]
            await asyncio.gather(*toggle_tasks)
            return {
                "instance_id": instance.id,
                "instance_name": instance.name,
                "status": "success",
                "matched": len(matching),
                "hosts": [h["host"] for h in matching],
            }
        except Exception as e:
            return {"instance_id": instance.id, "instance_name": instance.name, "status": "error", "error": str(e)}

    results = list(await asyncio.gather(*[_run(inst) for inst in instances]))

    action = "MASS_ENABLE_HOSTS" if body.enable else "MASS_DISABLE_HOSTS"
    run = await _save_run(
        db,
        run_type=action,
        user_id=current_user.id,
        parameters={"pattern": body.pattern, "enable": body.enable, "instance_ids": body.instance_ids},
        results=results,
    )

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        object_type="host",
        object_name=body.pattern,
        payload={"instances": len(instances), "enable": body.enable},
        result="success",
        ip_address=get_client_ip(request),
    )

    return {"run_id": run.id, "results": results}


@router.get("")
async def list_runs(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    result = await db.execute(
        select(OrchestrationRun)
        .order_by(desc(OrchestrationRun.started_at))
        .limit(limit)
        .offset(offset)
    )
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "type": r.type,
            "status": r.status,
            "parameters": r.parameters,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]


@router.get("/{run_id}")
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: HubUser = Depends(get_current_user),
):
    result = await db.execute(
        select(OrchestrationRun)
        .options(selectinload(OrchestrationRun.results))
        .where(OrchestrationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    return {
        "id": run.id,
        "type": run.type,
        "status": run.status,
        "parameters": run.parameters,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "results": [
            {
                "instance_name": r.instance_name,
                "status": r.status,
                "details": r.details,
            }
            for r in run.results
        ],
    }
