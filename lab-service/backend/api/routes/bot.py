"""Внутренние эндпоинты для Check Bot (приём чека)."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import verify_internal_token
from backend.database.session import get_db
from backend.services import orders as order_service
from backend.services.notification_service import NotificationService
from backend.services.receipt_delivery import deliver_admin_receipt
from backend.services.storage_service import FileValidationError, StorageService
from config.file_rules import AttachmentKind
from config.settings import get_settings

router = APIRouter(
    prefix="/bot", tags=["bot"], dependencies=[Depends(verify_internal_token)]
)


class ReceiptIn(BaseModel):
    telegram_id: int
    order_id: int | None = None  # подсказка: deep-link, #N в подписи или ответ на сообщение
    telegram_file_id: str
    kind: str  # photo | document
    original_name: str
    mime_type: str
    size_bytes: int
    user_chat_id: int | None = None
    user_message_id: int | None = None


@router.post("/receipt")
async def submit_receipt(
    payload: ReceiptIn,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
) -> dict:
    settings = get_settings()
    try:
        StorageService(settings).validate(
            AttachmentKind.RECEIPT,
            payload.original_name,
            payload.mime_type,
            payload.size_bytes,
        )
        order = await order_service.attach_receipt(
            session,
            payload.telegram_id,
            payload.order_id,
            telegram_file_id=payload.telegram_file_id,
            original_name=payload.original_name,
            mime_type=payload.mime_type,
            size_bytes=payload.size_bytes,
            user_chat_id=payload.user_chat_id,
            user_message_id=payload.user_message_id,
        )
    except (FileValidationError, order_service.OrderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Коммит до доставки: воркер/фоновая задача должны увидеть awaiting_review.
    await session.commit()
    if not payload.user_chat_id or not payload.user_message_id:
        raise HTTPException(status_code=400, detail="Нужны user_chat_id и user_message_id")

    queued = await NotificationService(settings.redis_url).enqueue_admin_receipt(
        order.id, payload.user_chat_id, payload.user_message_id
    )
    if not queued:
        background_tasks.add_task(
            deliver_admin_receipt,
            order.id,
            payload.user_chat_id,
            payload.user_message_id,
        )
    return order_service.serialize_order(order)
