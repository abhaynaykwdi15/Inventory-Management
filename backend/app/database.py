from collections.abc import Generator
from typing import Any

from fastapi import HTTPException, Request
from mysql.connector.pooling import MySQLConnectionPool

from app.config import Settings


def create_pool(settings: Settings) -> MySQLConnectionPool:
    return MySQLConnectionPool(
        pool_name="inventory_pool",
        pool_size=settings.pool_size,
        pool_reset_session=True,
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
        connection_timeout=5,
    )


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
