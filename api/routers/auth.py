from __future__ import annotations

import fastapi
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
import httpx

from config.manager import settings


router = fastapi.APIRouter(prefix="/auth", tags=["auth"])


@router.get("/signup", name="auth:signup")
async def signup_redirect() -> fastapi.responses.RedirectResponse:
    base = settings.CASDOOR_URL.rstrip("/")
    url = f"{base}/signup/{settings.CASDOOR_APP_NAME}"
    return fastapi.responses.RedirectResponse(url=url, status_code=fastapi.status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/signin", name="auth:signin")
async def signin_redirect(redirect_uri: str) -> fastapi.responses.RedirectResponse:
    base = settings.CASDOOR_URL.rstrip("/")
    url = (
        f"{base}/login/oauth/authorize?client_id={settings.CASDOOR_CLIENT_ID}"
        f"&response_type=code&redirect_uri={redirect_uri}&scope=read&state=casdoor"
    )
    return fastapi.responses.RedirectResponse(url=url, status_code=fastapi.status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/callback", name="auth:callback")
async def auth_callback(code: str, state: str, redirect_uri: str = "") -> dict:
    token_url = settings.CASDOOR_URL.rstrip("/") + "/api/login/oauth/access_token"
    auth = httpx.BasicAuth(settings.CASDOOR_CLIENT_ID, settings.CASDOOR_CLIENT_SECRET)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_url,
            auth=auth,
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        token_payload = resp.json()
    return token_payload


@router.post("/login", name="auth:login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    token_url = settings.CASDOOR_URL.rstrip("/") + "/api/login/oauth/access_token"
    auth = httpx.BasicAuth(settings.CASDOOR_CLIENT_ID, settings.CASDOOR_CLIENT_SECRET)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_url,
            auth=auth,
            data={
                "grant_type": "password",
                "username": form_data.username,
                "password": form_data.password,
                "scope": "read",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code == 400:
            raise fastapi.HTTPException(status_code=fastapi.status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        resp.raise_for_status()
        token_payload = resp.json()
    return token_payload


