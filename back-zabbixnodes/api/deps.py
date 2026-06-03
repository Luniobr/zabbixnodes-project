from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import decode_access_token
from models.user import HubUser, UserInstancePermission

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> HubUser:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

    result = await db.execute(select(HubUser).where(HubUser.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou não encontrado")
    return user


def require_superadmin(current_user: HubUser = Depends(get_current_user)) -> HubUser:
    if current_user.role != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a superadmin")
    return current_user


async def check_instance_access(
    user: HubUser,
    instance_id: int,
    db: AsyncSession,
    require_write: bool = False,
) -> None:
    if user.role == "superadmin":
        return
    result = await db.execute(
        select(UserInstancePermission).where(
            UserInstancePermission.user_id == user.id,
            UserInstancePermission.instance_id == instance_id,
        )
    )
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a esta instância")
    if require_write and not perm.can_write:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão de escrita necessária")


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
