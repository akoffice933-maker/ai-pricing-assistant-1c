"""Проверка API-токена (Bearer)."""

import secrets
from typing import Optional

from fastapi import Header, HTTPException, status

from app import config


async def verify_api_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not config.API_TOKEN:
        # Разрешено только вне production (см. проверку при старте в config.py).
        return
    expected = f"Bearer {config.API_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )
