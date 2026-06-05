import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.exc import IntegrityError

from api.v1.router import router as api_router
from core.config import settings
from core.database import AsyncSessionLocal
from core.security import hash_password
from models.user import HubUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zabbixnodes")


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


# Healthcheck (usado pelo HEALTHCHECK do Docker)
@app.get("/health")
async def health():
    return {"status": "ok"}
