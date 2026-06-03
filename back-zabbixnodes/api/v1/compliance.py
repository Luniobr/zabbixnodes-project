import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_client_ip, get_current_user, require_superadmin
from core.database import get_db
from models.instance import Instance
from models.orchestration import OrchestrationResult, OrchestrationRun
from models.user import HubUser
from services import audit as audit_svc
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/compliance", tags=["compliance"])


class AnalyzeRequest(BaseModel):
    reference_instance_id: int
    template_name: str
    instance_ids: list[int] = []


class DiffRequest(BaseModel):
    reference_instance_id: int
    template_name: str
    target_instance_id: int


class FixRequest(BaseModel):
    reference_instance_id: int
    template_name: str
    instance_ids: list[int]


async def _get_instances(db: AsyncSession, instance_ids: list[int]) -> list[Instance]:
    if instance_ids:
        result = await db.execute(
            select(Instance).where(Instance.id.in_(instance_ids), Instance.is_active == True)
        )
    else:
        result = await db.execute(
            select(Instance).where(Instance.is_active == True)
        )
    return result.scalars().all()


async def _check_instance(
    instance: Instance,
    template_name: str,
    reference_items: int,
) -> dict:
    try:
        tmpl = await zabbix_svc.get_template_by_name(instance.url, instance.api_token, template_name)
        if not tmpl:
            return {
                "instance_id": instance.id,
                "instance_name": instance.name,
                "status": "absent",
                "reference_items": reference_items,
                "actual_items": None,
                "template_id": None,
            }
        actual_items = await zabbix_svc.count_template_items(instance.url, instance.api_token, tmpl["templateid"])
        status = "ok" if actual_items == reference_items else "divergent"
        return {
            "instance_id": instance.id,
            "instance_name": instance.name,
            "status": status,
            "reference_items": reference_items,
            "actual_items": actual_items,
            "template_id": tmpl["templateid"],
        }
    except Exception as e:
        return {
            "instance_id": instance.id,
            "instance_name": instance.name,
            "status": "error",
            "reference_items": reference_items,
            "actual_items": None,
            "template_id": None,
            "error": str(e),
        }


@router.post("/analyze")
async def analyze(
    body: AnalyzeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    ref_result = await db.execute(select(Instance).where(Instance.id == body.reference_instance_id))
    ref_instance = ref_result.scalar_one_or_none()
    if not ref_instance:
        raise HTTPException(status_code=404, detail="Instância de referência não encontrada")

    ref_tmpl = await zabbix_svc.get_template_by_name(
        ref_instance.url, ref_instance.api_token, body.template_name
    )
    if not ref_tmpl:
        raise HTTPException(status_code=404, detail=f"Template '{body.template_name}' não encontrado na instância de referência")

    reference_items = await zabbix_svc.count_template_items(
        ref_instance.url, ref_instance.api_token, ref_tmpl["templateid"]
    )

    target_ids = [i for i in body.instance_ids if i != body.reference_instance_id]
    targets = await _get_instances(db, target_ids)
    targets = [i for i in targets if i.id != body.reference_instance_id]

    tasks = [_check_instance(inst, body.template_name, reference_items) for inst in targets]
    results = await asyncio.gather(*tasks)

    run = OrchestrationRun(
        type="TEMPLATE_COMPLIANCE_AUDIT",
        triggered_by=current_user.id,
        parameters={
            "reference_instance_id": body.reference_instance_id,
            "reference_instance_name": ref_instance.name,
            "template_name": body.template_name,
            "reference_items": reference_items,
        },
        status="completed",
        finished_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()

    for r in results:
        db.add(OrchestrationResult(
            run_id=run.id,
            instance_id=r["instance_id"],
            instance_name=r["instance_name"],
            status=r["status"],
            details={k: v for k, v in r.items() if k not in ("instance_id", "instance_name", "status")},
        ))

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_COMPLIANCE_AUDIT",
        object_type="template",
        object_name=body.template_name,
        payload={"reference_instance": ref_instance.name, "targets": len(targets)},
        result="success",
        ip_address=get_client_ip(request),
    )
    await db.commit()

    return {
        "run_id": run.id,
        "template_name": body.template_name,
        "reference_instance": ref_instance.name,
        "reference_items": reference_items,
        "results": list(results),
    }


@router.post("/diff")
async def diff_detail(
    body: DiffRequest,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    ref_result = await db.execute(select(Instance).where(Instance.id == body.reference_instance_id))
    ref_instance = ref_result.scalar_one_or_none()
    if not ref_instance:
        raise HTTPException(404, "Instância de referência não encontrada")

    target_result = await db.execute(select(Instance).where(Instance.id == body.target_instance_id))
    target_instance = target_result.scalar_one_or_none()
    if not target_instance:
        raise HTTPException(404, "Instância alvo não encontrada")

    ref_tmpl = await zabbix_svc.get_template_by_name(
        ref_instance.url, ref_instance.api_token, body.template_name
    )
    if not ref_tmpl:
        raise HTTPException(404, f"Template '{body.template_name}' não encontrado na instância de referência")

    target_tmpl = await zabbix_svc.get_template_by_name(
        target_instance.url, target_instance.api_token, body.template_name
    )

    ref_items = await zabbix_svc.get_template_items(
        ref_instance.url, ref_instance.api_token, ref_tmpl["templateid"]
    )
    target_items = await zabbix_svc.get_template_items(
        target_instance.url, target_instance.api_token, target_tmpl["templateid"]
    ) if target_tmpl else []

    # Fields to exclude from the display payload (internal/runtime only)
    _display_exclude = frozenset({
        "itemid", "templateid", "hostid", "flags", "state", "error",
        "lastvalue", "lastclock", "prevvalue", "lastns",
        "formula", "multiplier", "delta",
    })

    def _clean(item: dict) -> dict:
        return {k: v for k, v in item.items() if k not in _display_exclude}

    ref_by_key = {item["key_"]: item for item in ref_items}
    target_by_key = {item["key_"]: item for item in target_items}

    items = []
    for key_, item in ref_by_key.items():
        target_item = target_by_key.get(key_)
        items.append({
            "key_": key_,
            "name": item["name"],
            "type": item.get("type", "0"),
            "status": "ok" if target_item else "absent",
            "ref_item": _clean(item),
            "target_item": _clean(target_item) if target_item else None,
        })
    for key_, item in target_by_key.items():
        if key_ not in ref_by_key:
            items.append({
                "key_": key_,
                "name": item["name"],
                "type": item.get("type", "0"),
                "status": "extra",
                "ref_item": None,
                "target_item": _clean(item),
            })

    # Sort: absent first, then extra, then ok; alphabetically within each group
    order = {"absent": 0, "extra": 1, "ok": 2}
    items.sort(key=lambda x: (order.get(x["status"], 9), x["name"].lower()))

    return {
        "template_name": body.template_name,
        "reference_instance": ref_instance.name,
        "target_instance": target_instance.name,
        "ref_total": len(ref_items),
        "target_total": len(target_items),
        "absent": sum(1 for i in items if i["status"] == "absent"),
        "extra": sum(1 for i in items if i["status"] == "extra"),
        "ok": sum(1 for i in items if i["status"] == "ok"),
        "items": items,
    }


@router.post("/fix")
async def fix(
    body: FixRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(require_superadmin),
):
    ref_result = await db.execute(select(Instance).where(Instance.id == body.reference_instance_id))
    ref_instance = ref_result.scalar_one_or_none()
    if not ref_instance:
        raise HTTPException(status_code=404, detail="Instância de referência não encontrada")

    ref_tmpl = await zabbix_svc.get_template_by_name(
        ref_instance.url, ref_instance.api_token, body.template_name
    )
    if not ref_tmpl:
        raise HTTPException(status_code=404, detail=f"Template '{body.template_name}' não encontrado na instância de referência")

    targets = await _get_instances(db, body.instance_ids)

    async def _fix_instance(instance: Instance) -> dict:
        try:
            target_tmpl = await zabbix_svc.get_template_by_name(
                instance.url, instance.api_token, body.template_name
            )
            if not target_tmpl:
                return {
                    "instance_id": instance.id,
                    "instance_name": instance.name,
                    "status": "error",
                    "error": "Template ausente na instância alvo — importe o template base manualmente antes de sincronizar itens",
                }

            sync_results = await zabbix_svc.sync_template_items(
                ref_instance.url, ref_instance.api_token, ref_tmpl["templateid"],
                instance.url, instance.api_token, target_tmpl["templateid"],
            )

            created = [r for r in sync_results if r["created"]]
            failed = [r for r in sync_results if not r["created"]]

            if not sync_results:
                status = "ok"
            elif failed and not created:
                status = "error"
            elif failed:
                status = "partial"
            else:
                status = "fixed"

            return {
                "instance_id": instance.id,
                "instance_name": instance.name,
                "status": status,
                "created": len(created),
                "failed": len(failed),
                "details": sync_results,
                "error": "; ".join(r.get("error", "") for r in failed) if failed else None,
            }
        except Exception as e:
            return {
                "instance_id": instance.id,
                "instance_name": instance.name,
                "status": "error",
                "error": str(e),
            }

    tasks = [_fix_instance(inst) for inst in targets]
    results = await asyncio.gather(*tasks)

    run = OrchestrationRun(
        type="TEMPLATE_COMPLIANCE_FIX",
        triggered_by=current_user.id,
        parameters={
            "reference_instance_id": body.reference_instance_id,
            "reference_instance_name": ref_instance.name,
            "template_name": body.template_name,
        },
        status="completed",
        finished_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()

    for r in results:
        db.add(OrchestrationResult(
            run_id=run.id,
            instance_id=r["instance_id"],
            instance_name=r["instance_name"],
            status=r["status"],
            details={k: v for k, v in r.items() if k not in ("instance_id", "instance_name", "status")},
        ))

    await audit_svc.record(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="TEMPLATE_COMPLIANCE_FIX",
        object_type="template",
        object_name=body.template_name,
        payload={"reference_instance": ref_instance.name, "targets": len(targets)},
        result="success",
        ip_address=get_client_ip(request),
    )
    await db.commit()

    return {"run_id": run.id, "results": list(results)}
