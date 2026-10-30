from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INVENTORY_",
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mysql_host: str = Field(default="127.0.0.1", min_length=1)
    mysql_port: int = Field(default=3306, ge=1, le=65535)
    mysql_database: str = Field(default="inventory_management", min_length=1)
    mysql_user: str = Field(min_length=1)
    mysql_password: str = Field(min_length=1)
    pool_size: int = Field(default=5, ge=1, le=32)
    auth_session_hours: int = Field(default=12, ge=1, le=720)
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    frontend_url: str = "http://localhost:5173"
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "Inventory Desk"
    smtp_starttls: bool = True
    smtp_use_ssl: bool = False

    @model_validator(mode="after")
    def validate_auth_and_mail_settings(self) -> "Settings":
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("SameSite=None cookies require HTTPS and secure cookies.")
        if self.smtp_starttls and self.smtp_use_ssl:
            raise ValueError("Configure either SMTP STARTTLS or SMTP SSL, not both.")
        return self


class CorsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INVENTORY_",
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ]
    )

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("CORS origins must be explicit HTTP(S) origins without paths.")
        return [origin.rstrip("/") for origin in origins]
