
from collections.abc import Generator
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request
from mysql.connector.pooling import MySQLConnectionPool

from app.config import Settings


_AUTH_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS app_users (
        user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(254) NOT NULL,
        pending_email VARCHAR(254),
        password_hash VARCHAR(255) NOT NULL,
        email_verified BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                               ON UPDATE CURRENT_TIMESTAMP(3),
        CONSTRAINT pk_app_users PRIMARY KEY (user_id),
        CONSTRAINT uq_app_users_email UNIQUE (email),
        CONSTRAINT uq_app_users_pending_email UNIQUE (pending_email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id BIGINT UNSIGNED NOT NULL,
        token_hash CHAR(64) NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        CONSTRAINT pk_user_sessions PRIMARY KEY (session_id),
        CONSTRAINT uq_user_sessions_token UNIQUE (token_hash),
        CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id)
            REFERENCES app_users (user_id) ON DELETE CASCADE,
        INDEX ix_user_sessions_expiry (expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS account_tokens (
        token_hash CHAR(64) NOT NULL,
        user_id BIGINT UNSIGNED NOT NULL,
        purpose VARCHAR(24) NOT NULL,
        expires_at DATETIME NOT NULL,
        created_at TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        CONSTRAINT pk_account_tokens PRIMARY KEY (token_hash),
        CONSTRAINT fk_account_tokens_user FOREIGN KEY (user_id)
            REFERENCES app_users (user_id) ON DELETE CASCADE,
        CONSTRAINT ck_account_tokens_purpose CHECK (
            purpose IN ('verify_email', 'change_email', 'reset_password')
        ),
        INDEX ix_account_tokens_user_purpose (user_id, purpose),
        INDEX ix_account_tokens_expiry (expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
)


def create_pool(settings: Settings) -> MySQLConnectionPool:
    ca_path = Path(settings.mysql_ssl_ca)

    if not ca_path.is_file():
        raise FileNotFoundError(
            f"TiDB Cloud CA certificate not found: {ca_path}"
        )

    return MySQLConnectionPool(
        pool_name="inventory_pool",
        pool_size=settings.pool_size,
        pool_reset_session=True,
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
        connection_timeout=10,
        ssl_ca=str(ca_path),
        ssl_verify_cert=True,
        ssl_verify_identity=True,
    )


def ensure_auth_schema(pool: MySQLConnectionPool) -> None:
    """Create missing account tables without replacing existing account data."""
    connection = pool.get_connection()
    try:
        with connection.cursor() as cursor:
            for statement in _AUTH_SCHEMA_STATEMENTS:
                cursor.execute(statement)
    finally:
        connection.close()


def get_connection(request: Request) -> Generator[Any, None, None]:
    pool = getattr(request.app.state, "pool", None)

    if pool is None:
        detail = getattr(
            request.app.state,
            "database_error",
            "MySQL database is not configured.",
        )
        raise HTTPException(status_code=503, detail=detail)

    connection = pool.get_connection()
    try:
        yield connection
    finally:
        connection.close()
