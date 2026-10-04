from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.domain.order_status import OrderStatus
from backend.models.base import Base, TimestampMixin, utcnow


# Р’ SQLite Р°РІС‚РѕРёРЅРєСЂРµРјРµРЅС‚ СЂР°Р±РѕС‚Р°РµС‚ С‚РѕР»СЊРєРѕ Сѓ INTEGER PRIMARY KEY (РЅСѓР¶РЅРѕ РґР»СЏ Р»РѕРєР°Р»СЊРЅС‹С… С‚РµСЃС‚РѕРІ).
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")


def created_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    photo_url: Mapped[str | None] = mapped_column(String(512))
    language_code: Mapped[str | None] = mapped_column(String(8))

    orders: Mapped[list[Order]] = relationship(back_populates="user")
    credentials: Mapped[list[SubjectCredential]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SubjectCredential(Base, TimestampMixin):
    """Логин/пароль студента от платформы предмета. Пароль хранится только зашифрованным."""

    __tablename__ = "subject_credentials"
    __table_args__ = (UniqueConstraint("user_id", "subject"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(8))
    login: Mapped[str] = mapped_column(String(128))
    password_encrypted: Mapped[str] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="credentials")


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)

    labs: Mapped[list[Lab]] = relationship(
        secondary="lab_languages", back_populates="languages"
    )


class Lab(Base):
    __tablename__ = "labs"
    __table_args__ = (UniqueConstraint("subject", "lab_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(8), index=True)
    lab_number: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = created_at_column()

    languages: Mapped[list[Language]] = relationship(
        secondary="lab_languages", back_populates="labs"
    )


class LabLanguage(Base):
    __tablename__ = "lab_languages"

    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), primary_key=True)
    language_id: Mapped[int] = mapped_column(ForeignKey("languages.id"), primary_key=True)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=OrderStatus.AWAITING_PAYMENT, index=True
    )
    total_price: Mapped[int] = mapped_column(Integer)
    admin_comment: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    attachments: Mapped[list[Attachment]] = relationship(back_populates="order")
    github_links: Mapped[list[GithubLink]] = relationship(back_populates="order")
    payment: Mapped[Payment | None] = relationship(back_populates="order", uselist=False)
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        back_populates="order"
    )


class OrderItem(Base):
    """РћРґРЅР° РІС‹Р±СЂР°РЅРЅР°СЏ Р»Р°Р±РѕСЂР°С‚РѕСЂРЅР°СЏ РІРЅСѓС‚СЂРё Р·Р°РєР°Р·Р°. Р¦РµРЅР° вЂ” СЃРЅРёРјРѕРє РЅР° РјРѕРјРµРЅС‚ Р·Р°РєР°Р·Р°."""

    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "lab_id"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"))
    language_id: Mapped[int | None] = mapped_column(ForeignKey("languages.id"))
    price: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")
    lab: Mapped[Lab] = relationship()
    language: Mapped[Language | None] = relationship()


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    storage_path: Mapped[str | None] = mapped_column(String(512))
    original_name: Mapped[str] = mapped_column(String(256))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    telegram_file_id: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = created_at_column()

    order: Mapped[Order] = relationship(back_populates="attachments")


class GithubLink(Base):
    __tablename__ = "github_links"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    link_type: Mapped[str] = mapped_column(String(16))  # repo | file
    created_at: Mapped[datetime] = created_at_column()

    order: Mapped[Order] = relationship(back_populates="github_links")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    receipt_attachment_id: Mapped[int | None] = mapped_column(ForeignKey("attachments.id"))
    # Сообщение клиента с чеком (User Bot) и сообщение проверки (Admin Bot).
    user_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    user_message_id: Mapped[int | None] = mapped_column(BigInteger)
    admin_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    admin_message_id: Mapped[int | None] = mapped_column(BigInteger)
    confirmed_by: Mapped[int | None] = mapped_column(BigInteger)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()

    order: Mapped[Order] = relationship(back_populates="payment")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    old_status: Mapped[str | None] = mapped_column(String(32))
    new_status: Mapped[str] = mapped_column(String(32))
    changed_by: Mapped[int] = mapped_column(BigInteger, default=0)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()

    order: Mapped[Order] = relationship(back_populates="status_history")

