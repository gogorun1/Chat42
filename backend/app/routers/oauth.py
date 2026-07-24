import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import set_auth_cookie
from app.core.security import create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth/42", tags=["oauth"])
settings = get_settings()

AUTHORIZE_URL = "https://api.intra.42.fr/oauth/authorize"
TOKEN_URL = "https://api.intra.42.fr/oauth/token"
USER_INFO_URL = "https://api.intra.42.fr/v2/me"
STATE_COOKIE_NAME = "oauth_state"


@router.get("/login")
async def login_with_42() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": settings.ft_client_id,
        "redirect_uri": settings.ft_redirect_uri,
        "response_type": "code",
        "scope": "public",
        "state": state,
    }
    response = RedirectResponse(f"{AUTHORIZE_URL}?{urlencode(params)}")
    # SameSite=Lax (not Strict): this cookie must survive the top-level
    # cross-site redirect 42 sends the browser back through on /callback.
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=300,
        path="/",
    )
    return response


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    expected_state = request.cookies.get(STATE_COOKIE_NAME)
    if not expected_state or expected_state != state:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid OAuth state")

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.ft_client_id,
                "client_secret": settings.ft_client_secret,
                "code": code,
                "redirect_uri": settings.ft_redirect_uri,
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Failed to exchange code with 42")
        access_token = token_res.json()["access_token"]

        me_res = await client.get(USER_INFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if me_res.status_code != 200:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Failed to fetch 42 profile")
        profile = me_res.json()

    email = profile["email"]
    ft_login = profile["login"]

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(email=email, ft_login=ft_login)
        db.add(user)
    elif user.ft_login is None:
        user.ft_login = ft_login

    await db.commit()
    await db.refresh(user)

    redirect = RedirectResponse(settings.frontend_url)
    redirect.delete_cookie(STATE_COOKIE_NAME, path="/")
    set_auth_cookie(redirect, create_access_token(user.email))
    return redirect
