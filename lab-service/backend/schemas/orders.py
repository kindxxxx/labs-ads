from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class CreateOrderRequest(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    lab_id: int
    language_id: int | None = None


class AttachmentOut(BaseModel):
    id: int
    kind: str
    original_name: str
    mime_type: str
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GithubLinkOut(BaseModel):
    id: int
    url: str
    link_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    status: str
    status_label: str
    subject: str
    lab_number: int
    language: str | None
    total_price: int
    attachments: list[AttachmentOut] = Field(default_factory=list)
    github_links: list[GithubLinkOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AddGithubRequest(BaseModel):
    url: HttpUrl


class ChangeStatusRequest(BaseModel):
    status: str
    comment: str | None = None
    admin_telegram_id: int


class PaymentActionRequest(BaseModel):
    reason: str | None = None
