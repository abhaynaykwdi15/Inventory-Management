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


def init_db(pool: MySQLConnectionPool) -> None:
    """Automatically create required tables if they do not exist to prevent error 1146."""
    connection = pool.get_connection()
    try:
        cursor = connection.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                sku VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(100),
                quantity INT DEFAULT 0,
                price DECIMAL(10, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Transactions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT,
                type VARCHAR(50) NOT NULL,
                quantity INT NOT NULL,
                reference VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        """)

        # 4. Audit Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit (
                id INT AUTO_INCREMENT PRIMARY KEY,
                action VARCHAR(255) NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()
        cursor.close()
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