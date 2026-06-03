from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from core.database import get_db
from models.user import HubUser
from schemas.dashboard import DashboardResponse
from services.dashboard import get_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: HubUser = Depends(get_current_user),
):
    return await get_dashboard(db, user_id=current_user.id, is_superadmin=current_user.role == "superadmin")
