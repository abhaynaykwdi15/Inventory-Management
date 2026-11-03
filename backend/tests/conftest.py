from collections.abc import Generator
from unittest.mock import MagicMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import create_app
from app.routers.auth import require_user


class FakePool:
    def get_connection(self) -> MagicMock:
        return MagicMock()

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


@pytest.fixture
def connection() -> FakeConnection:
    return FakeConnection()


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
    connection: FakeConnection,
) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("INVENTORY_MYSQL_USER", "unit_test_user")
    monkeypatch.setenv("INVENTORY_MYSQL_PASSWORD", "not-a-real-password")

    from app import database

    monkeypatch.setattr(database, "create_pool", Mock(return_value=FakePool()))
    application = create_app()
    application.dependency_overrides[get_connection] = lambda: connection
    application.dependency_overrides[require_user] = lambda: {
        "user_id": 1,
        "full_name": "Test User",
        "email": "test@example.com",
        "pending_email": None,
        "email_verified": True,
    }
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
