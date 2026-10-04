"""Доступы студента к платформам предметов. Пароль шифруется Fernet (AES-128 + HMAC)."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import SubjectCredential, User
from config.labs import SUBJECT_PLATFORMS
from config.settings import get_settings


class CredentialsError(ValueError):
    pass


def _fernet() -> Fernet:
    key = get_settings().credentials_key
    if not key:
        raise CredentialsError("CREDENTIALS_KEY не задан на сервере")
    return Fernet(key.encode())


async def list_for_user(session: AsyncSession, user: User) -> dict[str, SubjectCredential]:
    rows = await session.scalars(
        select(SubjectCredential).where(SubjectCredential.user_id == user.id)
    )
    return {row.subject: row for row in rows}


async def save(
    session: AsyncSession, user: User, subject: str, login: str, password: str
) -> SubjectCredential:
    if subject not in SUBJECT_PLATFORMS:
        raise CredentialsError(f"Неизвестный предмет {subject}")
    login = login.strip()
    if not login or not password:
        raise CredentialsError("Нужны логин и пароль")

    row = await session.scalar(
        select(SubjectCredential).where(
            SubjectCredential.user_id == user.id, SubjectCredential.subject == subject
        )
    )
    if row is None:
        row = SubjectCredential(user_id=user.id, subject=subject)
        session.add(row)
    row.login = login
    row.password_encrypted = _fernet().encrypt(password.encode()).decode()
    await session.flush()
    return row


async def delete(session: AsyncSession, user: User, subject: str) -> None:
    row = await session.scalar(
        select(SubjectCredential).where(
            SubjectCredential.user_id == user.id, SubjectCredential.subject == subject
        )
    )
    if row is not None:
        await session.delete(row)
        await session.flush()


def decrypt_password(row: SubjectCredential) -> str:
    try:
        return _fernet().decrypt(row.password_encrypted.encode()).decode()
    except InvalidToken as exc:
        raise CredentialsError("Не удалось расшифровать пароль (сменился ключ?)") from exc


def public_view(subject: str, row: SubjectCredential | None) -> dict:
    platform = SUBJECT_PLATFORMS[subject]
    return {
        "subject": subject,
        "title": platform.title,
        "platform": platform.platform,
        "login": row.login if row else None,
        "has_password": row is not None,
        "updated_at": row.updated_at.isoformat() if row else None,
    }
