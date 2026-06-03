import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.v1.router import router as api_router
from core.config import settings
from core.database import AsyncSessionLocal, engine
from core.security import hash_password
from models.user import HubUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zabbixnodes")

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _create_admin_user()
    yield


async def _create_admin_user():
    async with AsyncSessionLocal() as db:
        try:
            user = HubUser(
                username=settings.ADMIN_USER,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role="superadmin",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            logger.info(f"Admin user '{settings.ADMIN_USER}' created.")
        except IntegrityError:
            await db.rollback()
            logger.info(f"Admin user '{settings.ADMIN_USER}' already exists, skipping.")


limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.API_RATE_LIMIT}/minute"])

app = FastAPI(
    title="ZabbixNodes",
    description="Plataforma de Gerenciamento Multi-Instância Zabbix",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# API routes
app.include_router(api_router)

# Static files and templates
static_dir = FRONTEND_DIR / "static"
templates_dir = FRONTEND_DIR / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/instances", response_class=HTMLResponse)
async def instances_page(request: Request):
    return templates.TemplateResponse("instances/list.html", {"request": request})


@app.get("/instances/new", response_class=HTMLResponse)
async def new_instance_page(request: Request):
    return templates.TemplateResponse("instances/form.html", {"request": request, "instance": None})


@app.get("/instances/{instance_id}/edit", response_class=HTMLResponse)
async def edit_instance_page(request: Request, instance_id: int):
    return templates.TemplateResponse("instances/form.html", {"request": request, "instance_id": instance_id})


@app.get("/hosts", response_class=HTMLResponse)
async def hosts_page(request: Request):
    return templates.TemplateResponse("hosts/list.html", {"request": request})


@app.get("/host-groups", response_class=HTMLResponse)
async def host_groups_page(request: Request):
    return templates.TemplateResponse("host_groups/list.html", {"request": request})


@app.get("/proxies", response_class=HTMLResponse)
async def proxies_page(request: Request):
    return templates.TemplateResponse("proxies/list.html", {"request": request})


@app.get("/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    return templates.TemplateResponse("templates/list.html", {"request": request})


@app.get("/triggers", response_class=HTMLResponse)
async def triggers_page(request: Request):
    return templates.TemplateResponse("triggers/list.html", {"request": request})


@app.get("/items", response_class=HTMLResponse)
async def items_page(request: Request):
    return templates.TemplateResponse("items/list.html", {"request": request})


@app.get("/instance-groups", response_class=HTMLResponse)
async def instance_groups_page(request: Request):
    return templates.TemplateResponse("instance_groups/list.html", {"request": request})


@app.get("/compliance", response_class=HTMLResponse)
async def compliance_page(request: Request):
    return templates.TemplateResponse("compliance/index.html", {"request": request})


@app.get("/orchestration", response_class=HTMLResponse)
async def orchestration_page(request: Request):
    return templates.TemplateResponse("orchestration/index.html", {"request": request})


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users/list.html", {"request": request})


@app.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    return templates.TemplateResponse("audit/list.html", {"request": request})


@app.get("/health", response_class=HTMLResponse)
async def health_page(request: Request):
    return templates.TemplateResponse("health/index.html", {"request": request})


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    return templates.TemplateResponse("reports/index.html", {"request": request})
