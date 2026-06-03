from fastapi import APIRouter

from api.v1 import auth, audit, compliance, dashboard, health, host_groups, hosts, instances, items, orchestration, proxies, reports, templates, triggers, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(instances.router)
router.include_router(instances.groups_router)
router.include_router(dashboard.router)
router.include_router(hosts.router)
router.include_router(host_groups.router)
router.include_router(proxies.router)
router.include_router(templates.router)
router.include_router(users.router)
router.include_router(compliance.router)
router.include_router(audit.router)
router.include_router(orchestration.router)
router.include_router(triggers.router)
router.include_router(items.router)
router.include_router(health.router)
router.include_router(reports.router)
