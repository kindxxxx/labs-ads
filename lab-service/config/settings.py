"""Центральные настройки приложения (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Bots ---
    user_bot_token: str = Field(default="", alias="USER_BOT_TOKEN")
    admin_bot_token: str = Field(default="", alias="ADMIN_BOT_TOKEN")
    admin_id: int = Field(default=0, alias="ADMIN_ID")

    # --- Database / Supabase ---
    database_url: str = Field(
        default="postgresql+asyncpg://labs:labs@postgres:5432/labs",
        alias="DATABASE_URL",
    )
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_project_ref: str = Field(
        default="rslndrfinxxvpxcbcjkd", alias="SUPABASE_PROJECT_REF"
    )
    supabase_db_password: str = Field(default="", alias="SUPABASE_DB_PASSWORD")

    # --- Redis / Queue ---
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # --- Server ---
    base_url: str = Field(default="http://localhost:8000", alias="BASE_URL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    internal_api_token: str = Field(default="change-me", alias="INTERNAL_API_TOKEN")

    # --- Storage ---
    storage_root: Path = Field(default=BASE_DIR / "storage", alias="STORAGE_ROOT")
    temp_ttl_hours: int = Field(default=24, alias="TEMP_TTL_HOURS")
    max_attachment_size_mb: int = Field(default=20, alias="MAX_ATTACHMENT_SIZE_MB")
    max_receipt_size_mb: int = Field(default=10, alias="MAX_RECEIPT_SIZE_MB")

    # --- Payment ---
    payment_instructions: str = Field(
        default="Переведите сумму на Kaspi и отправьте чек в этот чат.",
        alias="PAYMENT_INSTRUCTIONS",
    )
    # Номер карты / телефон Kaspi — показывается в Mini App с кнопкой «копировать».
    payment_requisites: str = Field(default="", alias="PAYMENT_REQUISITES")
    payment_recipient: str = Field(default="", alias="PAYMENT_RECIPIENT")
    user_bot_username: str = Field(default="", alias="USER_BOT_USERNAME")
    check_bot_username: str = Field(default="", alias="CHECK_BOT_USERNAME")

    # --- Mini App ---
    miniapp_url: str = Field(default="", alias="MINIAPP_URL")
    miniapp_origins: str = Field(default="*", alias="MINIAPP_ORIGINS")
    init_data_max_age_seconds: int = Field(default=86400, alias="INIT_DATA_MAX_AGE_SECONDS")

    # --- Credentials encryption (Fernet key) ---
    credentials_key: str = Field(default="", alias="CREDENTIALS_KEY")

    # --- Security ---
    rate_limit_orders_per_hour: int = Field(default=5, alias="RATE_LIMIT_ORDERS_PER_HOUR")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.miniapp_origins.split(",") if o.strip()]

    @property
    def resolved_database_url(self) -> str:
        """DATABASE_URL или сборка из SUPABASE_DB_PASSWORD + project ref."""
        url = self.database_url
        if not self.supabase_db_password:
            return url
        if "[YOUR-PASSWORD]" in url:
            return url.replace("[YOUR-PASSWORD]", self.supabase_db_password)
        if self.supabase_project_ref and "supabase.co" not in url:
            host = f"db.{self.supabase_project_ref}.supabase.co"
            return (
                f"postgresql+asyncpg://postgres:{self.supabase_db_password}"
                f"@{host}:5432/postgres"
            )
        return url

    @property
    def uses_supabase_host(self) -> bool:
        return "supabase.co" in self.resolved_database_url

    @field_validator("storage_root", mode="before")
    @classmethod
    def _path(cls, v: str | Path) -> Path:
        return Path(v)

    @property
    def uploads_dir(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def temp_dir(self) -> Path:
        return self.storage_root / "temp"

    def ensure_storage_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
