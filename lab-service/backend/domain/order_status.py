"""Статусы заказа и допустимые переходы."""

from __future__ import annotations

from enum import StrEnum


class OrderStatus(StrEnum):
    AWAITING_PAYMENT = "awaiting_payment"
    AWAITING_REVIEW = "awaiting_review"
    PAID = "paid"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


ORDER_STATUS_LABELS: dict[OrderStatus, str] = {
    OrderStatus.AWAITING_PAYMENT: "Ожидает оплату",
    OrderStatus.AWAITING_REVIEW: "Ожидает проверки",
    OrderStatus.PAID: "Оплачен",
    OrderStatus.IN_PROGRESS: "В работе",
    OrderStatus.COMPLETED: "Готово",
    OrderStatus.REJECTED: "Отклонён",
}

USER_NOTIFICATIONS: dict[OrderStatus, str] = {
    OrderStatus.AWAITING_REVIEW: "🟡 Чек по заказу #{id} получен. Ожидайте подтверждения оплаты.",
    OrderStatus.PAID: "🟢 ОПЛАТА ПОДТВЕРЖДЕНА\n\nЗаказ #{id} оплачен.",
    OrderStatus.IN_PROGRESS: "🟢 ОПЛАТА ПОДТВЕРЖДЕНА\n\nЗаказ #{id} принят в работу.",
    OrderStatus.COMPLETED: "✅ ЗАКАЗ ГОТОВ\n\nЛабораторные по заказу #{id} выполнены.",
    OrderStatus.REJECTED: "❌ Заказ #{id} отклонён.",
}

PAYMENT_REJECTED_TEXT = (
    "🔴 Оплата не подтверждена.\n\n"
    "Не удалось найти оплату по заказу #{id}. Проверьте перевод и пришлите чек ещё раз."
)


def user_message(status: OrderStatus, order_id: int) -> str:
    return USER_NOTIFICATIONS.get(status, "Заказ #{id}: " + status.value).format(id=order_id)

# from_status -> set of allowed to_status
ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.AWAITING_PAYMENT: frozenset(
        {OrderStatus.AWAITING_REVIEW, OrderStatus.REJECTED}
    ),
    # Подтверждение чека сразу запускает работу: awaiting_review → in_progress.
    OrderStatus.AWAITING_REVIEW: frozenset(
        {
            OrderStatus.PAID,
            OrderStatus.IN_PROGRESS,
            OrderStatus.REJECTED,
            OrderStatus.AWAITING_PAYMENT,
        }
    ),
    OrderStatus.PAID: frozenset({OrderStatus.IN_PROGRESS, OrderStatus.REJECTED}),
    OrderStatus.IN_PROGRESS: frozenset({OrderStatus.COMPLETED, OrderStatus.REJECTED}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.REJECTED: frozenset({OrderStatus.AWAITING_PAYMENT}),
}


def can_transition(from_status: OrderStatus, to_status: OrderStatus) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, frozenset())
