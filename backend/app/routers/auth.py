import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserOut
from app.security import (
    OAUTH_STATE_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    create_session_token,
    encrypt_secret,
)
from app.services import github_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/login")
async def github_login():
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
        "scope": "repo read:user",
        "state": state,
        "allow_signup": "true",
    }
    resp = RedirectResponse(f"https://github.com/login/oauth/authorize?{urlencode(params)}")
    # short-lived, httponly cookie used purely for CSRF protection on the callback
    # resp.set_cookie(OAUTH_STATE_COOKIE_NAME, state, httponly=True, secure=settings.is_production,
    #                  samesite="lax", max_age=600)
    # return resp
    resp.set_cookie(OAUTH_STATE_COOKIE_NAME, state, httponly=True, secure=True,
                 samesite="none", max_age=600)
    return resp


@router.get("/github/callback")
async def github_callback(request: Request, code: str, state: str, db: AsyncSession = Depends(get_db)):
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    if not expected_state or expected_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state (possible CSRF attempt)")

    access_token = await github_client.exchange_code_for_token(code)
    gh_user = await github_client.get_authenticated_user(access_token)

    result = await db.execute(select(User).where(User.github_id == gh_user["id"]))
    user = result.scalar_one_or_none()
    encrypted = encrypt_secret(access_token)

    if user:
        user.access_token_encrypted = encrypted
        user.username = gh_user["login"]
        user.avatar_url = gh_user.get("avatar_url")
    else:
        user = User(
            github_id=gh_user["id"],
            username=gh_user["login"],
            avatar_url=gh_user.get("avatar_url"),
            access_token_encrypted=encrypted,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    session_token = create_session_token(str(user.id))
    resp = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
    resp.delete_cookie(OAUTH_STATE_COOKIE_NAME)
    # resp.set_cookie(
    #     SESSION_COOKIE_NAME, session_token, httponly=True, secure=settings.is_production,
    #     samesite="lax", max_age=7 * 24 * 3600,
    # )
    resp.set_cookie(
        SESSION_COOKIE_NAME, session_token, httponly=True, secure=True,
        samesite="none", max_age=7 * 24 * 3600,
    )
    return resp


@router.post("/logout")
async def logout():
    resp = RedirectResponse(settings.FRONTEND_URL)
    resp.delete_cookie(SESSION_COOKIE_NAME)
    return resp


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
