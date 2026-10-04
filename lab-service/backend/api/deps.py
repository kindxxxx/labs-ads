from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models import User
from backend.services.orders import upsert_user
from backend.services.telegram_auth import InitDataError, validate_init_data
from config.settings import Settings, get_settings


def get_app_settings() -> Settings:
    return get_settings()


async def verify_internal_token(
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
    settings: Settings = Depends(get_app_settings),
) -> None:
    if not x_internal_token or x_internal_token != settings.internal_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


async def verify_admin(
    _: None = Depends(verify_internal_token),
    x_admin_telegram_id: int | None = Header(default=None, alias="X-Admin-Telegram-Id"),
    settings: Settings = Depends(get_app_settings),
) -> int:
    # Заголовок с ID сам по себе подделывается, поэтому только в паре с internal token.
    if x_admin_telegram_id is None or x_admin_telegram_id != settings.admin_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return x_admin_telegram_id


async def current_miniapp_user(
    x_telegram_init_data: str = Header(default="", alias="X-Telegram-Init-Data"),
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db),
) -> User:
    try:
        tg_user = validate_init_data(
            x_telegram_init_data,
            settings.user_bot_token,
            settings.init_data_max_age_seconds,
        )
    except InitDataError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return await upsert_user(session, tg_user)
