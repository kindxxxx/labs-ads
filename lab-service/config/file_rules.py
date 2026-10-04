"""Правила валидации загружаемых файлов."""

from __future__ import annotations

from enum import StrEnum


class AttachmentKind(StrEnum):
    CODE = "code"
    RECEIPT = "receipt"
    NOTES = "notes"
    IMAGE = "image"
    OTHER = "other"


ALLOWED_MIME: dict[AttachmentKind, frozenset[str]] = {
    AttachmentKind.CODE: frozenset(
        {
            "text/plain",
            "text/x-python",
            "application/x-python-code",
            "text/x-c++src",
            "text/x-java-source",
        }
    ),
    AttachmentKind.RECEIPT: frozenset(
        {
            "image/jpeg",
            "image/png",
            "application/pdf",
        }
    ),
    AttachmentKind.NOTES: frozenset(
        {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        }
    ),
    AttachmentKind.IMAGE: frozenset({"image/jpeg", "image/png", "image/webp"}),
    AttachmentKind.OTHER: frozenset({"application/octet-stream"}),
}

ALLOWED_EXTENSIONS: dict[AttachmentKind, frozenset[str]] = {
    AttachmentKind.CODE: frozenset({".py", ".cpp", ".h", ".java", ".c", ".txt"}),
    AttachmentKind.RECEIPT: frozenset({".jpg", ".jpeg", ".png", ".pdf"}),
    AttachmentKind.NOTES: frozenset({".pdf", ".docx", ".txt"}),
    AttachmentKind.IMAGE: frozenset({".jpg", ".jpeg", ".png", ".webp"}),
    AttachmentKind.OTHER: frozenset(),
}

GITHUB_URL_PREFIXES = (
    "https://github.com/",
    "https://raw.githubusercontent.com/",
)
