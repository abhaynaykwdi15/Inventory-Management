from pathlib import Path
from unittest.mock import Mock

from fastapi import HTTPException
from mysql.connector import Error as MySQLDatabaseError
from fastapi.testclient import TestClient

from app.config import Settings
from app.config import CorsSettings
from app.repositories import inventory
from app.services.database_errors import run_write
from app.routers.auth import require_user
from app.services.auth_security import hash_password, verify_password
from app.repositories import accounts


def test_settings_load_backend_env_file_independent_of_working_directory():
    assert Settings.model_config["env_file"] == (
        Path(__file__).resolve().parents[1] / ".env"
    )


def test_health_checks_the_database(client, monkeypatch):
    monkeypatch.setattr(inventory, "health_check", Mock(return_value=None))

    response = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5173"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_api_status_does_not_depend_on_mysql(client):
    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_current_source_registers_account_route(client):
    client.app.dependency_overrides.pop(require_user)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Sign in to continue."


def test_development_cors_defaults_include_vite_port_5174():
    settings = CorsSettings(_env_file=None)

    assert "http://127.0.0.1:5174" in settings.cors_origins


def test_api_uses_configured_cors_origins(monkeypatch):
    from app.main import create_app

    monkeypatch.setenv(
        "INVENTORY_CORS_ORIGINS",
        '["https://inventory.example"]',
    )

    application = create_app()

    assert application.user_middleware[0].kwargs["allow_origins"] == [
        "https://inventory.example"
    ]


def test_registration_requires_smtp_before_creating_an_account(client, monkeypatch):
    from app.repositories import accounts

    client.app.state.settings.smtp_host = None
    client.app.state.settings.smtp_from_email = None
    account_lookup = Mock()
    monkeypatch.setattr(accounts, "email_is_unavailable", account_lookup)

    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": "signup@example.invalid",
            "password": "a-long-test-password",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Email delivery is not configured. Set INVENTORY_SMTP_HOST and "
            "INVENTORY_SMTP_FROM_EMAIL in the backend environment "
            "(Render: service Environment settings)."
        )
    }
    account_lookup.assert_not_called()


def test_inventory_routes_require_an_authenticated_account(client):
    client.app.dependency_overrides.pop(require_user)

    response = client.get("/api/items")

    assert response.status_code == 401
    assert response.json()["detail"] == "Sign in to continue."


def test_password_hash_is_salted_and_verifies_without_storing_plaintext():
    first = hash_password("a-long-test-password")
    second = hash_password("a-long-test-password")

    assert first != second
    assert "a-long-test-password" not in first
    assert verify_password("a-long-test-password", first)
    assert not verify_password("wrong-password", first)


def test_login_sets_http_only_session_cookie_without_returning_a_password_hash(
    client,
    connection,
    monkeypatch,
):
    stored_hash = hash_password("a-long-test-password")
    monkeypatch.setattr(
        accounts,
        "get_account_by_email",
        Mock(return_value={
            "user_id": 7,
            "full_name": "Test Account",
            "email": "verified@example.com",
            "pending_email": None,
            "password_hash": stored_hash,
            "email_verified": True,
        }),
    )
    create_session = Mock(return_value=None)
    monkeypatch.setattr(accounts, "create_session", create_session)

    response = client.post(
        "/api/auth/login",
        json={"email": "verified@example.com", "password": "a-long-test-password"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "verified@example.com"
    assert "password_hash" not in response.json()
    cookie = response.headers["set-cookie"].lower()
    assert "inventory_session=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    create_session.assert_called_once()
    assert connection.commits == 1


def test_logout_revokes_session_and_clears_cookie(client, connection, monkeypatch):
    delete_session = Mock(return_value=None)
    monkeypatch.setattr(accounts, "delete_session", delete_session)
    client.cookies.set("inventory_session", "test-session-token")

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    assert "inventory_session=" in response.headers["set-cookie"]
    assert "max-age=0" in response.headers["set-cookie"].lower()
    delete_session.assert_called_once_with(connection, "test-session-token")
    assert connection.commits == 1


def test_item_categories_route_is_not_captured_as_an_item_id(client, monkeypatch):
    monkeypatch.setattr(inventory, "list_item_categories", Mock(return_value=["Accessories", "Displays"]))

    response = client.get("/api/items/categories")

    assert response.status_code == 200
    assert response.json() == ["Accessories", "Displays"]


def test_api_starts_and_reports_missing_mysql_configuration(monkeypatch):
    from app.main import create_app

    monkeypatch.setenv("INVENTORY_MYSQL_USER", "")
    monkeypatch.setenv("INVENTORY_MYSQL_PASSWORD", "")

    with TestClient(create_app()) as test_client:
        response = test_client.get("/api/health")
        status_response = test_client.get("/api/status")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "MySQL credentials are not configured. Add them to backend/.env."
    }
    assert status_response.status_code == 200
    assert status_response.json() == {"status": "ok"}


def test_api_reports_mysql_login_rejection(monkeypatch):
    from app import database
    from app.main import create_app

    monkeypatch.setenv("INVENTORY_MYSQL_USER", "inventory_app")
    monkeypatch.setenv("INVENTORY_MYSQL_PASSWORD", "test-password")
    monkeypatch.setattr(
        database,
        "create_pool",
        Mock(
            side_effect=MySQLDatabaseError(
                msg="Access denied",
                errno=1045,
            )
        ),
    )

    with TestClient(create_app()) as test_client:
        response = test_client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "MySQL rejected the configured login (error 1045). Verify "
            "INVENTORY_MYSQL_USER and INVENTORY_MYSQL_PASSWORD in backend/.env, "
            "and confirm the account is allowed from INVENTORY_MYSQL_HOST."
        )
    }


def test_dashboard_summary_uses_selected_period(client, monkeypatch):
    monkeypatch.setattr(
        inventory,
        "dashboard_summary",
        Mock(return_value={
            "period_days": 7,
            "total_unique_items": 5,
            "total_units_in_stock": 45,
            "low_stock_items": 3,
            "out_of_stock_items": 1,
            "stock_received_in_period": 0,
            "stock_issued_in_period": 0,
            "stock_by_category": [],
            "movement_by_day": [],
            "low_stock_comparison": [],
            "recent_transactions": [],
        }),
    )

    response = client.get("/api/dashboard/summary?period_days=7")

    assert response.status_code == 200
    assert response.json()["period_days"] == 7
    assert response.json()["total_unique_items"] == 5
    assert response.json()["total_units_in_stock"] == 45


def test_current_stock_report_passes_filters_and_returns_database_summary(
    client,
    connection,
    monkeypatch,
):
    report = {
        "items": [{
            "item_id": 7,
            "sku": "DEMO-KEY-001",
            "item_name": "Demo Keyboard",
            "category": "Accessories",
            "quantity_on_hand": 8,
            "reorder_level": 3,
            "updated_at": "2026-10-30T10:00:00",
        }],
        "total": 1,
        "limit": 10,
        "offset": 0,
        "summary": {
            "total_items": 1,
            "total_units": 8,
            "low_stock_items": 0,
            "out_of_stock_items": 0,
        },
    }
    list_report = Mock(return_value=report)
    monkeypatch.setattr(inventory, "list_current_stock_report", list_report)

    response = client.get(
        "/api/reports/current-stock",
        params={
            "search": "keyboard",
            "category": "Accessories",
            "item_id": 7,
            "sort_by": "quantity_on_hand",
            "direction": "desc",
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] == report["summary"]
    assert response.json()["items"][0]["quantity_on_hand"] == 8
    list_report.assert_called_once_with(
        connection,
        search="keyboard",
        category="Accessories",
        item_id=7,
        sort_by="quantity_on_hand",
        direction="desc",
        limit=10,
        offset=0,
    )


def test_current_stock_item_options_can_be_filtered_by_category(
    client,
    connection,
    monkeypatch,
):
    options = [{
        "item_id": 7,
        "item_name": "Demo Keyboard",
        "sku": "DEMO-KEY-001",
        "category": "Accessories",
    }]
    list_options = Mock(return_value=options)
    monkeypatch.setattr(inventory, "list_current_stock_item_options", list_options)

    response = client.get(
        "/api/reports/current-stock/items",
        params={"category": "Accessories"},
    )

    assert response.status_code == 200
    assert response.json() == options
    list_options.assert_called_once_with(connection, "Accessories")


def test_stock_receipt_commits_and_returns_server_result(client, connection, monkeypatch):
    monkeypatch.setattr(
        inventory,
        "add_stock",
        Mock(
            return_value={
                "message": "Stock received successfully.",
                "item_id": 1,
                "quantity_on_hand": 23,
            }
        ),
    )

    response = client.post(
        "/api/stock/in",
        json={"item_id": 1, "quantity": 3, "remarks": "demo receipt"},
    )

    assert response.status_code == 200
    assert response.json()["quantity_on_hand"] == 23
    assert connection.commits == 1
    assert connection.rollbacks == 0


def test_invalid_stock_quantity_is_rejected_before_database_call(client, monkeypatch):
    monkeypatch.setattr(
        inventory,
        "issue_stock",
        Mock(side_effect=AssertionError("Invalid input must not reach the repository.")),
    )

    response = client.post(
        "/api/stock/out",
        json={"item_id": 1, "quantity": -2},
    )

    assert response.status_code == 422
    assert response.json()["detail"]


def test_invalid_path_item_id_is_rejected(client):
    response = client.get("/api/items/not-an-integer")

    assert response.status_code == 422


def test_database_failure_rolls_back_without_exposing_driver_message(connection):
    def fail_write():
        raise MySQLDatabaseError("private connection detail")

    try:
        run_write(connection, fail_write)
    except HTTPException as error:
        assert error.status_code == 500
        assert error.detail == "The database operation failed."
    else:
        raise AssertionError("Expected a sanitized API error.")

    assert connection.commits == 0
    assert connection.rollbacks == 1


def test_insufficient_stock_signal_returns_conflict_and_rolls_back(connection):
    def fail_write():
        raise MySQLDatabaseError(
            msg="Insufficient stock for this issue.",
            errno=1644,
        )

    try:
        run_write(connection, fail_write)
    except HTTPException as error:
        assert error.status_code == 409
        assert error.detail == "Insufficient stock for this issue."
    else:
        raise AssertionError("Expected an insufficient-stock conflict.")

    assert connection.commits == 0
    assert connection.rollbacks == 1
