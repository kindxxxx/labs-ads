"""Проверка Telegram WebApp initData (регистрация/вход через Telegram).

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataError(ValueError):
    pass


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    photo_url: str | None
    language_code: str | None


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int) -> TelegramUser:
    if not init_data:
        raise InitDataError("initData отсутствует")
    if not bot_token:
        raise InitDataError("USER_BOT_TOKEN не задан на сервере")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("hash отсутствует")

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise InitDataError("Неверная подпись initData")

    auth_date = int(pairs.get("auth_date", "0"))
    if max_age_seconds and time.time() - auth_date > max_age_seconds:
        raise InitDataError("initData устарел")

    try:
        raw = json.loads(pairs["user"])
    except (KeyError, json.JSONDecodeError) as exc:
        raise InitDataError("user отсутствует в initData") from exc

    return TelegramUser(
        id=int(raw["id"]),
        first_name=raw.get("first_name"),
        last_name=raw.get("last_name"),
        username=raw.get("username"),
        photo_url=raw.get("photo_url"),
        language_code=raw.get("language_code"),
    )
