"""Эндпоинты Telegram Mini App. Авторизация — заголовок X-Telegram-Init-Data."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.deps import current_miniapp_user
from backend.database.session import get_db
from backend.models import Lab, User
from backend.services import credentials as cred_service
from backend.services import orders as order_service
from config.labs import SUBJECT_PLATFORMS
from config.settings import get_settings

router = APIRouter(prefix="/miniapp", tags=["miniapp"])


class OrderItemIn(BaseModel):
    lab_id: int
    language: str | None = None


class CreateOrderIn(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=20)


class CredentialIn(BaseModel):
    login: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


@router.post("/auth")
async def auth(user: User = Depends(current_miniapp_user)) -> dict:
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "photo_url": user.photo_url,
    }


@router.get("/settings")
async def public_settings() -> dict:
    s = get_settings()
    return {
        "bot_username": s.user_bot_username,
        "check_bot_username": s.check_bot_username or s.user_bot_username,
        "payment_requisites": s.payment_requisites,
        "payment_recipient": s.payment_recipient,
        "payment_instructions": s.payment_instructions,
    }


@router.get("/catalog")
async def catalog(session: AsyncSession = Depends(get_db)) -> list[dict]:
    labs = await session.scalars(
        select(Lab)
        .where(Lab.is_active.is_(True))
        .options(selectinload(Lab.languages))
        .order_by(Lab.subject, Lab.lab_number)
    )
    return [
        {
            "id": lab.id,
            "subject": lab.subject,
            "lab_number": lab.lab_number,
            "price": lab.price,
            "description": lab.description,
            "requirements": lab.requirements,
            "languages": [lang.name for lang in lab.languages],
        }
        for lab in labs
    ]


@router.get("/credentials")
async def my_credentials(
    user: User = Depends(current_miniapp_user),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    saved = await cred_service.list_for_user(session, user)
    return [cred_service.public_view(s, saved.get(s)) for s in SUBJECT_PLATFORMS]


@router.put("/credentials/{subject}")
async def save_credential(
    subject: str,
    payload: CredentialIn,
    user: User = Depends(current_miniapp_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    try:
        row = await cred_service.save(session, user, subject, payload.login, payload.password)
    except cred_service.CredentialsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return cred_service.public_view(subject, row)


@router.delete("/credentials/{subject}")
async def delete_credential(
    subject: str,
    user: User = Depends(current_miniapp_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    if subject not in SUBJECT_PLATFORMS:
        raise HTTPException(status_code=404, detail="Неизвестный предмет")
    await cred_service.delete(session, user, subject)
    return cred_service.public_view(subject, None)


@router.get("/orders")
async def my_orders(
    user: User = Depends(current_miniapp_user),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    orders = await order_service.list_user_orders(session, user.id)
    return [order_service.serialize_order(o) for o in orders]


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: CreateOrderIn,
    user: User = Depends(current_miniapp_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    try:
        order = await order_service.create_order(
            session, user, [(i.lab_id, i.language) for i in payload.items]
        )
    except order_service.OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    saved = await cred_service.list_for_user(session, user)
    missing = sorted({i.lab.subject for i in order.items} - saved.keys())
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Укажи логин и пароль для: {', '.join(missing)}"
        )

    # Админ узнаёт о заказе только вместе с чеком — одно сообщение на заказ.
    return order_service.serialize_order(order)
