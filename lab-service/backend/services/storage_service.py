"""Сохранение и валидация файлов."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from config.file_rules import ALLOWED_EXTENSIONS, ALLOWED_MIME, AttachmentKind
from config.settings import Settings


class FileValidationError(ValueError):
    pass


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        settings.ensure_storage_dirs()

    def validate(
        self, kind: AttachmentKind, filename: str, mime_type: str, size_bytes: int
    ) -> None:
        max_mb = (
            self._settings.max_receipt_size_mb
            if kind == AttachmentKind.RECEIPT
            else self._settings.max_attachment_size_mb
        )
        if size_bytes > max_mb * 1024 * 1024:
            raise FileValidationError(f"Файл больше {max_mb} МБ")

        ext = Path(filename).suffix.lower()
        allowed_ext = ALLOWED_EXTENSIONS.get(kind, frozenset())
        if allowed_ext and ext not in allowed_ext:
            raise FileValidationError(f"Расширение {ext} не разрешено для {kind}")

        allowed_mime = ALLOWED_MIME.get(kind, frozenset())
        if allowed_mime and mime_type not in allowed_mime:
            raise FileValidationError(f"MIME {mime_type} не разрешён для {kind}")

    def build_order_path(self, order_id: int, filename: str) -> Path:
        safe_name = f"{uuid4().hex}_{Path(filename).name}"
        dest = self._settings.uploads_dir / str(order_id) / safe_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        return dest
