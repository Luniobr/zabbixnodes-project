from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_current_user
from core.database import get_db
from models.audit_log import AuditLog
from models.instance import Instance
from models.user import HubUser, UserInstancePermission
from services.health_score import calculate_health_score
from services.reports import generate_pdf
from services import zabbix as zabbix_svc

router = APIRouter(prefix="/reports", tags=["reports"])


async def _accessible_instances(db: AsyncSession, user: HubUser) -> list[Instance]:
    query = select(Instance).options(selectinload(Instance.group)).where(Instance.is_active == True)
    if user.role != "superadmin":
        query = (
            query
            .join(UserInstancePermission, UserInstancePermission.instance_id == Instance.id)
            .where(UserInstancePermission.user_id == user.id)
        )
    result = await db.execute(query)
    return result.scalars().all()


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/health")
async def report_health(
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    """Relatório PDF — Health Score de todas as instâncias."""
    instances = await _accessible_instances(db, current_user)
    if not instances:
        raise HTTPException(status_code=404, detail="Nenhuma instância acessível")

    import asyncio
    scores = await asyncio.gather(
        *[calculate_health_score(i.url, i.api_token) for i in instances],
        return_exceptions=True,
    )

    rows = []
    for inst, score in zip(instances, scores):
        if isinstance(score, Exception):
            rows.append({"name": inst.name, "group": inst.group.name if inst.group else "—",
                         "url": inst.url, "score": None, "label": "Erro", "color": "offline",
                         "error": str(score), "dimensions": {}})
        else:
            rows.append({"name": inst.name, "group": inst.group.name if inst.group else "—",
                         "url": inst.url, **score})

    rows.sort(key=lambda r: ({"health-critical": 0, "health-warning": 1,
                               "health-healthy": 2, "health-excellent": 3}.get(r.get("color", ""), 4)))

    pdf = await generate_pdf("pdf_health.html", {
        "rows": rows,
        "total": len(rows),
        "generated_by": current_user.username,
    })
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _pdf_response(pdf, f"zabbixnodes_health_{ts}.pdf")


@router.get("/inventory")
async def report_inventory(
    instance_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    """Relatório PDF — Inventário de hosts."""
    instances = await _accessible_instances(db, current_user)
    if instance_id:
        instances = [i for i in instances if i.id == instance_id]
    if not instances:
        raise HTTPException(status_code=404, detail="Nenhuma instância acessível")

    import asyncio

    async def _fetch(inst: Instance):
        try:
            hosts = await zabbix_svc.list_hosts(inst.url, inst.api_token)
            return {"instance": inst.name, "group": inst.group.name if inst.group else "—",
                    "hosts": hosts, "error": None}
        except Exception as e:
            return {"instance": inst.name, "group": inst.group.name if inst.group else "—",
                    "hosts": [], "error": str(e)}

    sections = await asyncio.gather(*[_fetch(i) for i in instances])
    total_hosts = sum(len(s["hosts"]) for s in sections)

    pdf = await generate_pdf("pdf_inventory.html", {
        "sections": sections,
        "total_hosts": total_hosts,
        "generated_by": current_user.username,
    })
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _pdf_response(pdf, f"zabbixnodes_inventory_{ts}.pdf")


@router.get("/audit")
async def report_audit(
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to:   str | None = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    """Relatório PDF — Log de auditoria. Restrito a superadmin."""
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Acesso restrito a superadmin")

    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.where(AuditLog.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import timedelta
            dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
            query = query.where(AuditLog.created_at < dt_to)
        except ValueError:
            pass

    result = await db.execute(query)
    logs = result.scalars().all()

    pdf = await generate_pdf("pdf_audit.html", {
        "logs": logs,
        "total": len(logs),
        "date_from": date_from or "—",
        "date_to": date_to or "—",
        "generated_by": current_user.username,
    })
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _pdf_response(pdf, f"zabbixnodes_audit_{ts}.pdf")


@router.get("/triggers")
async def report_triggers(
    instance_id: int | None = Query(None),
    min_severity: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    """Relatório PDF — Triggers ativas."""
    instances = await _accessible_instances(db, current_user)
    if instance_id:
        instances = [i for i in instances if i.id == instance_id]
    if not instances:
        raise HTTPException(status_code=404, detail="Nenhuma instância acessível")

    import asyncio

    SEV_NAMES = {0: "Não classificado", 1: "Informação", 2: "Warning",
                 3: "Average", 4: "High", 5: "Disaster"}

    async def _fetch(inst: Instance):
        try:
            triggers = await zabbix_svc.list_triggers(
                inst.url, inst.api_token, only_problems=True, min_severity=min_severity
            )
            for t in triggers:
                t["priority_name"] = SEV_NAMES.get(int(t.get("priority", 0)), "?")
            return {"instance": inst.name, "group": inst.group.name if inst.group else "—",
                    "triggers": triggers, "error": None}
        except Exception as e:
            return {"instance": inst.name, "group": inst.group.name if inst.group else "—",
                    "triggers": [], "error": str(e)}

    sections = await asyncio.gather(*[_fetch(i) for i in instances])
    total_triggers = sum(len(s["triggers"]) for s in sections)

    pdf = await generate_pdf("pdf_triggers.html", {
        "sections": sections,
        "total_triggers": total_triggers,
        "min_severity": SEV_NAMES.get(min_severity, "Todos"),
        "generated_by": current_user.username,
    })
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return _pdf_response(pdf, f"zabbixnodes_triggers_{ts}.pdf")
