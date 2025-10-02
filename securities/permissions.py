from __future__ import annotations

import os
import fastapi
from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import loguru

from config.manager import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_casdoor_public_key() -> Optional[str]:
    configured_value = (settings.CASDOOR_CERTIFICATE or "").strip()
    if not configured_value:
        return None
    if os.path.exists(configured_value) and os.path.isfile(configured_value):
        try:
            with open(configured_value, "r", encoding="utf-8") as f:
                cert = f.read().strip()
        except Exception:
            return None
    else:
        cert = configured_value
    if not cert.startswith("-----BEGIN CERTIFICATE-----"):
        cert = "-----BEGIN CERTIFICATE-----\n" + cert + "\n-----END CERTIFICATE-----\n"
    return cert


async def get_current_customer_id(token: Annotated[str, fastapi.Depends(oauth2_scheme)]) -> int:
    public_key_pem = _get_casdoor_public_key()
    if not public_key_pem:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Casdoor certificate missing")
    try:
        claims = jwt.decode(token, public_key_pem, algorithms=["RS256"], options={"verify_aud": False})
    except JWTError:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = claims.get("sub") or claims.get("preferred_username") or claims.get("name")
    if user_id is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    loguru.logger.info(f"user_id: {user_id}")

    return user_id


def authorize_order_access(current_user_id: int, order_customer_id: int) -> None:
    if current_user_id != order_customer_id:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order",
        )


