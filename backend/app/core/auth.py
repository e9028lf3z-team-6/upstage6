from datetime import datetime, timedelta
from app.core.settings import get_settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_session, User

try:
    from jose import jwt, JWTError
    _JOSE_AVAILABLE = True
    _JOSE_IMPORT_ERROR = None
except Exception as exc:
    jwt = None
    JWTError = Exception
    _JOSE_AVAILABLE = False
    _JOSE_IMPORT_ERROR = exc

settings = get_settings()
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token", auto_error=False)


def _ensure_jose() -> None:
    if not _JOSE_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail=f"JWT library not available: {_JOSE_IMPORT_ERROR}. Install python-jose.",
        )


def create_access_token(data: dict):
    _ensure_jose()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
):
    if not token:
        return None
    if not _JOSE_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail=f"JWT library not available: {_JOSE_IMPORT_ERROR}. Install python-jose.",
        )
        
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
        
    async with session as s:
        result = await s.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user


async def get_required_user(user: User = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
