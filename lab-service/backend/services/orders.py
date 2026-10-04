"""Жизненный цикл заказа: выбор лаб → оплата → чек → подтверждение → работа."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.order_status import ORDER_STATUS_LABELS, OrderStatus, can_transition
from config.labs import contest_id, lab_contest_url
from backend.models import (
    Lab,
    Language,
    Order,
    OrderItem,
    OrderStatusHistory,
    Payment,
    User,
)
from backend.services.telegram_auth import TelegramUser


class OrderError(ValueError):
    pass


_ORDER_LOAD = (
    selectinload(Order.items).selectinload(OrderItem.lab),
    selectinload(Order.items).selectinload(OrderItem.language),
    selectinload(Order.payment),
    selectinload(Order.user),
)


async def upsert_user(session: AsyncSession, tg: TelegramUser) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == tg.id))
    if user is None:
        user = User(telegram_id=tg.id)
        session.add(user)
    user.username = tg.username
    user.first_name = tg.first_name
    user.last_name = tg.last_name
    user.photo_url = tg.photo_url
    user.language_code = tg.language_code
    await session.flush()
    return user


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.scalar(
        select(Order)
        .where(Order.id == order_id)
        .options(*_ORDER_LOAD)
        .execution_options(populate_existing=True)
    )


async def list_user_orders(session: AsyncSession, user_id: int) -> list[Order]:
    result = await session.scalars(
        select(Order)
        .where(Order.user_id == user_id)
        .options(*_ORDER_LOAD)
        .order_by(Order.created_at.desc())
    )
    return list(result)


async def create_order(
    session: AsyncSession, user: User, items: list[tuple[int, str | None]]
) -> Order:
    if not items:
        raise OrderError("Не выбрано ни одной лабораторной")
    lab_ids = [lab_id for lab_id, _ in items]
    if len(set(lab_ids)) != len(lab_ids):
        raise OrderError("Лабораторная выбрана дважды")

    labs = {
        lab.id: lab
        for lab in await session.scalars(
            select(Lab)
            .where(Lab.id.in_(lab_ids), Lab.is_active.is_(True))
            .options(selectinload(Lab.languages))
        )
    }

    order = Order(user_id=user.id, status=OrderStatus.AWAITING_PAYMENT, total_price=0)
    for lab_id, language_name in items:
        lab = labs.get(lab_id)
        if lab is None:
            raise OrderError(f"Лабораторная {lab_id} недоступна")
        language: Language | None = None
        if lab.languages:
            by_name = {lang.name: lang for lang in lab.languages}
            language = by_name.get(language_name or lab.languages[0].name)
            if language is None:
                raise OrderError(
                    f"{lab.subject} Lab {lab.lab_number}: язык {language_name} недоступен"
                )
        order.items.append(
            OrderItem(lab_id=lab.id, language_id=language.id if language else None, price=lab.price)
        )
        order.total_price += lab.price

    session.add(order)
    await session.flush()
    session.add(Payment(order_id=order.id, amount=order.total_price, status="pending"))
    session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=None,
            new_status=OrderStatus.AWAITING_PAYMENT,
            changed_by=user.telegram_id,
        )
    )
    await session.flush()
    return await get_order(session, order.id)


async def _set_status(
    session: AsyncSession,
    order: Order,
    new_status: OrderStatus,
    changed_by: int,
    comment: str | None = None,
) -> None:
    old = OrderStatus(order.status)
    if not can_transition(old, new_status):
        raise OrderError(f"Переход {old} → {new_status} запрещён")
    order.status = new_status
    session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=old,
            new_status=new_status,
            changed_by=changed_by,
            comment=comment,
        )
    )


async def find_order_for_receipt(
    session: AsyncSession, telegram_id: int, hinted_order_id: int | None
) -> Order:
    """Заказ, к которому относится чек: подсказанный (#N / deep-link) или последний неоплаченный."""
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        raise OrderError("Сначала оформите заказ в приложении, затем пришлите чек.")

    waiting = (OrderStatus.AWAITING_PAYMENT, OrderStatus.AWAITING_REVIEW)
    query = select(Order.id).where(Order.user_id == user.id, Order.status.in_(waiting))
    order_id = None
    if hinted_order_id is not None:
        order_id = await session.scalar(query.where(Order.id == hinted_order_id))
    if order_id is None:
        order_id = await session.scalar(query.order_by(Order.created_at.desc()).limit(1))
    if order_id is None:
        raise OrderError("Нет заказа, который ждёт чек.")
    return await get_order(session, order_id)


async def attach_receipt(
    session: AsyncSession,
    telegram_id: int,
    hinted_order_id: int | None,
    *,
    telegram_file_id: str,
    original_name: str,
    mime_type: str,
    size_bytes: int,
    user_chat_id: int | None = None,
    user_message_id: int | None = None,
) -> Order:
    order = await find_order_for_receipt(session, telegram_id, hinted_order_id)
    if order.status == OrderStatus.AWAITING_REVIEW:
        raise OrderError(f"Чек по заказу #{order.id} уже получен. Ожидайте подтверждения оплаты.")

    # Чек не пишем в БД: файл остаётся в Telegram и копируется админу.
    _ = (telegram_file_id, original_name, mime_type, size_bytes, user_chat_id, user_message_id)
    order.payment.receipt_attachment_id = None
    order.payment.status = "pending"
    order.payment.user_chat_id = None
    order.payment.user_message_id = None
    order.payment.admin_chat_id = None
    order.payment.admin_message_id = None
    await _set_status(session, order, OrderStatus.AWAITING_REVIEW, telegram_id)
    await session.flush()
    return order


async def revert_receipt(session: AsyncSession, order_id: int) -> Order | None:
    """Чек не удалось доставить админу — даём пользователю прислать его заново."""
    order = await get_order(session, order_id)
    if order is None or order.status != OrderStatus.AWAITING_REVIEW:
        return order
    await _set_status(session, order, OrderStatus.AWAITING_PAYMENT, 0, "Чек не доставлен админу")
    await session.flush()
    return order


async def remember_admin_message(
    session: AsyncSession, order_id: int, chat_id: int, message_id: int
) -> None:
    order = await get_order(session, order_id)
    if order and order.payment:
        order.payment.admin_chat_id = chat_id
        order.payment.admin_message_id = message_id
        await session.flush()


async def confirm_payment(session: AsyncSession, order_id: int, admin_id: int) -> tuple[Order, bool]:
    """Возвращает (заказ, изменился_ли). Повторное нажатие кнопки ничего не ломает."""
    order = await get_order(session, order_id)
    if order is None:
        raise OrderError("Заказ не найден")
    if order.payment.status == "confirmed":
        return order, False
    if order.status != OrderStatus.AWAITING_REVIEW:
        raise OrderError("Нет чека на проверке")
    order.payment.status = "confirmed"
    order.payment.confirmed_by = admin_id
    order.payment.confirmed_at = datetime.now(UTC)
    await _set_status(session, order, OrderStatus.IN_PROGRESS, admin_id, "Оплата подтверждена")
    await session.flush()
    return order, True


async def reject_payment(
    session: AsyncSession, order_id: int, admin_id: int, reason: str | None
) -> tuple[Order, bool]:
    order = await get_order(session, order_id)
    if order is None:
        raise OrderError("Заказ не найден")
    if order.payment.status in ("confirmed", "rejected"):
        return order, False
    if order.status != OrderStatus.AWAITING_REVIEW:
        raise OrderError("Нет чека на проверке")
    order.payment.status = "rejected"
    order.payment.rejection_reason = reason
    order.admin_comment = reason
    # Пользователь может прислать исправленный чек.
    await _set_status(session, order, OrderStatus.AWAITING_PAYMENT, admin_id, reason)
    await session.flush()
    return order, True


async def complete_order(session: AsyncSession, order_id: int, admin_id: int) -> tuple[Order, bool]:
    order = await get_order(session, order_id)
    if order is None:
        raise OrderError("Заказ не найден")
    if order.status == OrderStatus.COMPLETED:
        return order, False
    if order.status != OrderStatus.IN_PROGRESS:
        raise OrderError("Сначала подтвердите оплату")
    await _set_status(session, order, OrderStatus.COMPLETED, admin_id)
    await session.flush()
    return order, True


def serialize_order(order: Order, *, with_user: bool = False) -> dict:
    data = {
        "id": order.id,
        "status": order.status,
        "status_label": ORDER_STATUS_LABELS[OrderStatus(order.status)],
        "total_price": order.total_price,
        "admin_comment": order.admin_comment,
        "payment_status": order.payment.status if order.payment else None,
        "user_message_id": order.payment.user_message_id if order.payment else None,
        "admin_message_id": order.payment.admin_message_id if order.payment else None,
        "items": [
            {
                "lab_id": item.lab_id,
                "subject": item.lab.subject,
                "lab_number": item.lab.lab_number,
                "contest_id": contest_id(item.lab.subject, item.lab.lab_number),
                "url": lab_contest_url(item.lab.subject, item.lab.lab_number),
                "language": item.language.name if item.language else None,
                "price": item.price,
            }
            for item in order.items
        ],
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }
    if with_user:
        data["user"] = {
            "telegram_id": order.user.telegram_id,
            "username": order.user.username,
            "first_name": order.user.first_name,
        }
    return data
