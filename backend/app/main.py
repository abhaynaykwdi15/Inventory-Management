from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mysql.connector import Error as MySQLDatabaseError
from pydantic import ValidationError

from app import database
from app.config import CorsSettings, Settings
from app.routers import auth, audit, dashboard, health, items, reports, stock, transactions


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    try:
        settings = Settings()
    except ValidationError as error:
        application.state.pool = None
        missing_mysql_credentials = any(
            issue["loc"] and issue["loc"][0] in {"mysql_user", "mysql_password"}
            for issue in error.errors()
        )
        if missing_mysql_credentials:
            application.state.database_error = (
                "MySQL credentials are not configured. Add them to backend/.env."
            )
            logger.error("MySQL configuration is incomplete; database routes will return HTTP 503.")
        else:
            application.state.database_error = (
                "Backend configuration is invalid. Check the settings in backend/.env."
            )
            logger.error(
                "Backend configuration validation failed: %s",
                error.errors(include_input=False),
            )
        yield
        return

    application.state.settings = settings
    try:
        pool = database.create_pool(settings)
        application.state.pool = pool
        
        # Automatically create database tables on startup to solve Error 1146
        database.init_db(pool)
        
        application.state.database_error = None
    except MySQLDatabaseError as error:
        application.state.pool = None
        if error.errno == 1045:
            application.state.database_error = (
                "MySQL rejected the configured login (error 1045). Verify "
                "INVENTORY_MYSQL_USER and INVENTORY_MYSQL_PASSWORD in backend/.env, "
                "and confirm the account is allowed from INVENTORY_MYSQL_HOST."
            )
        else:
            application.state.database_error = (
                "MySQL is unavailable or rejected the configured credentials."
            )
        logger.error(
            "Could not create the MySQL connection pool (error code %s).",
            error.errno,
        )
        yield
        return

    yield


def create_app() -> FastAPI:
    cors_settings = CorsSettings()
    application = FastAPI(
        title="Inventory Management API",
        description="MySQL-backed inventory management API for fictional demonstration data.",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    origins = getattr(cors_settings, "origins", None) or [
        "https://inventory-management-881a-git-main-abhaynaykwdi15.vercel.app",
        "http://localhost:5173"
    ]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    application.include_router(auth.router, prefix="/api")
    application.include_router(health.router, prefix="/api")
    application.include_router(dashboard.router, prefix="/api")
    application.include_router(items.router, prefix="/api")
    application.include_router(stock.router, prefix="/api")
    application.include_router(transactions.router, prefix="/api")
    application.include_router(reports.router, prefix="/api")
    application.include_router(audit.router, prefix="/api")
    return application


app = create_app()