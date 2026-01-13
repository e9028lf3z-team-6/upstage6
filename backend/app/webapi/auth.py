import uuid
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.core.settings import get_settings
from app.core.db import get_session, User
from app.core.auth import create_access_token, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()
settings = get_settings()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    # For local development, if request.url_for is http but we need https, we might need to adjust.
    # But usually http is fine for localhost.
    return await oauth.google.authorize_redirect(request, str(redirect_uri))

@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request, session: AsyncSession = Depends(get_session)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print(f"OAuth error: {e}")
        raise HTTPException(status_code=400, detail="OAuth authorization failed")
        
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    email = user_info.get('email')
    name = user_info.get('name')
    picture = user_info.get('picture')

    async with session as s:
        # Check if user exists
        result = await s.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                name=name,
                picture=picture
            )
            s.add(user)
            await s.commit()
            await s.refresh(user)

    # Generate JWT
    access_token = create_access_token(data={"sub": user.id})
    
    # Redirect to frontend with token
    frontend_url = f"{settings.frontend_origin}?token={access_token}"
    return RedirectResponse(url=frontend_url)

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture
    }
