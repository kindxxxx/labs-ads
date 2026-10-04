"""HTTP-клиент ботов к Backend API."""

from __future__ import annotations

from typing import Any

import httpx

from config.settings import Settings


class ApiClient:
    def __init__(self, settings: Settings) -> None:
        self._base = settings.base_url.rstrip("/")
        self._headers = {"X-Internal-Token": settings.internal_api_token}

    async def get_subjects(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self._base}/catalog/subjects", headers=self._headers)
            r.raise_for_status()
            return r.json()

    async def get_labs(self, subject: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base}/catalog/labs",
                params={"subject": subject},
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()

    async def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self._base}/orders",
                json=payload,
                headers=self._headers,
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json()

    async def submit_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self._base}/bot/receipt", json=payload, headers=self._headers, timeout=30.0
            )
            r.raise_for_status()
            return r.json()

    async def _admin(
        self, method: str, path: str, admin_id: int, json: dict | None = None
    ) -> Any:
        async with httpx.AsyncClient() as client:
            r = await client.request(
                method,
                f"{self._base}/admin{path}",
                json=json,
                headers={**self._headers, "X-Admin-Telegram-Id": str(admin_id)},
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json()

    async def admin_payment_action(
        self, order_id: int, admin_id: int, action: str, reason: str | None = None
    ) -> dict[str, Any]:
        body = {"reason": reason} if action == "reject" else None
        return await self._admin("POST", f"/orders/{order_id}/payment/{action}", admin_id, body)

    async def admin_complete(self, order_id: int, admin_id: int) -> dict[str, Any]:
        return await self._admin("POST", f"/orders/{order_id}/complete", admin_id)

    async def admin_credentials(self, order_id: int, admin_id: int) -> list[dict[str, Any]]:
        return await self._admin("GET", f"/orders/{order_id}/credentials", admin_id)

    async def get_user_orders(self, telegram_id: int) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self._base}/users/{telegram_id}/orders",
                headers=self._headers,
            )
            r.raise_for_status()
            return r.json()
