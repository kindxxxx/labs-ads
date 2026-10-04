from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import verify_admin
from backend.database.session import get_db
from backend.domain.order_status import PAYMENT_REJECTED_TEXT, OrderStatus, user_message
from backend.models import Order
from backend.schemas.orders import PaymentActionRequest
from backend.services import credentials as cred_service
from backend.services import orders as order_service
from backend.services.notification_service import NotificationService
from config.labs import contest_id, lab_contest_url
from config.settings import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])


def _notifier() -> NotificationService:
    return NotificationService(get_settings().redis_url)


@router.get("/orders")
async def list_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, le=100),
    session: AsyncSession = Depends(get_db),
    _: int = Depends(verify_admin),
) -> list[dict]:
    query = select(Order.id).order_by(Order.created_at.desc()).limit(limit)
    if status_filter:
        query = query.where(Order.status == status_filter)
    ids = list(await session.scalars(query))
    orders = [await order_service.get_order(session, i) for i in ids]
    return [order_service.serialize_order(o, with_user=True) for o in orders if o]


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
    _: int = Depends(verify_admin),
) -> dict:
    order = await order_service.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order_service.serialize_order(order, with_user=True)


@router.get("/orders/{order_id}/credentials")
async def order_credentials(
    order_id: int,
    session: AsyncSession = Depends(get_db),
    _: int = Depends(verify_admin),
) -> list[dict]:
    order = await order_service.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.status not in (OrderStatus.IN_PROGRESS, OrderStatus.PAID):
        raise HTTPException(status_code=403, detail="Доступы выдаются только после оплаты")

    saved = await cred_service.list_for_user(session, order.user)
    result = []
    for item in sorted(order.items, key=lambda i: (i.lab.subject, i.lab.lab_number)):
        row = saved.get(item.lab.subject)
        result.append(
            {
                "subject": item.lab.subject,
                "lab_number": item.lab.lab_number,
                "contest_id": contest_id(item.lab.subject, item.lab.lab_number),
                "url": lab_contest_url(item.lab.subject, item.lab.lab_number),
                "login": row.login if row else None,
                "password": cred_service.decrypt_password(row) if row else None,
            }
        )
    return result


@router.post("/orders/{order_id}/payment/confirm")
async def confirm_payment(
    order_id: int,
    session: AsyncSession = Depends(get_db),
    admin_id: int = Depends(verify_admin),
) -> dict:
    try:
        order, changed = await order_service.confirm_payment(session, order_id, admin_id)
    except order_service.OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if changed:
        await session.commit()
        await _notifier().enqueue_user_message(
            order.user.telegram_id, user_message(OrderStatus.IN_PROGRESS, order.id)
        )
    return order_service.serialize_order(order, with_user=True)


@router.post("/orders/{order_id}/payment/reject")
async def reject_payment(
    order_id: int,
    payload: PaymentActionRequest | None = None,
    session: AsyncSession = Depends(get_db),
    admin_id: int = Depends(verify_admin),
) -> dict:
    reason = payload.reason if payload else None
    try:
        order, changed = await order_service.reject_payment(session, order_id, admin_id, reason)
    except order_service.OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if changed:
        await session.commit()
        await _notifier().enqueue_user_message(
            order.user.telegram_id, PAYMENT_REJECTED_TEXT.format(id=order.id)
        )
    return order_service.serialize_order(order, with_user=True)


@router.post("/orders/{order_id}/complete")
async def complete_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
    admin_id: int = Depends(verify_admin),
) -> dict:
    try:
        order, changed = await order_service.complete_order(session, order_id, admin_id)
    except order_service.OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if changed:
        await session.commit()
        await _notifier().enqueue_user_message(
            order.user.telegram_id, user_message(OrderStatus.COMPLETED, order.id)
        )
    return order_service.serialize_order(order, with_user=True)
