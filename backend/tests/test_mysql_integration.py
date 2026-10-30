import os
from collections.abc import Generator

import mysql.connector
import pytest

from app.config import Settings
from app.repositories.inventory import dashboard_summary, list_current_stock_report


pytestmark = pytest.mark.skipif(
    os.getenv("INVENTORY_RUN_MYSQL_INTEGRATION") != "1",
    reason="Set INVENTORY_RUN_MYSQL_INTEGRATION=1 to use the configured MySQL test database.",
)


@pytest.fixture
def mysql_connection() -> Generator[mysql.connector.MySQLConnection, None, None]:
    settings = Settings()
    connection = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
        autocommit=False,
    )
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def test_stock_receipt_updates_balance_and_transaction_atomically(mysql_connection):
    item_id = 5
    with mysql_connection.cursor() as cursor:
        cursor.execute(
            "SELECT quantity_on_hand FROM stock WHERE item_id = %s",
            (item_id,),
        )
        original_quantity = cursor.fetchone()[0]
        cursor.callproc("add_stock", [item_id, 2, "Integration test receipt", "test-user"])
        cursor.execute(
            "SELECT quantity_on_hand FROM stock WHERE item_id = %s",
            (item_id,),
        )
        assert cursor.fetchone()[0] == original_quantity + 2
        cursor.execute(
            """
            SELECT COUNT(*) FROM stock_transactions
             WHERE item_id = %s
               AND transaction_type = 'IN'
               AND remarks = %s
            """,
            (item_id, "Integration test receipt"),
        )
        assert cursor.fetchone()[0] == 1


def test_issue_rejects_insufficient_stock(mysql_connection):
    with mysql_connection.cursor() as cursor:
        cursor.execute(
            "SELECT quantity_on_hand FROM stock WHERE item_id = %s",
            (4,),
        )
        assert cursor.fetchone()[0] == 0
        with pytest.raises(mysql.connector.Error):
            cursor.callproc("issue_stock", [4, 1, "Integration test issue", "test-user"])


def test_stock_issue_updates_balance_and_writes_out_transaction(mysql_connection):
    item_id = 1
    with mysql_connection.cursor() as cursor:
        cursor.execute(
            "SELECT quantity_on_hand FROM stock WHERE item_id = %s",
            (item_id,),
        )
        original_quantity = cursor.fetchone()[0]
        cursor.callproc("issue_stock", [item_id, 1, "Integration test issue", "test-user"])
        cursor.execute(
            "SELECT quantity_on_hand FROM stock WHERE item_id = %s",
            (item_id,),
        )
        assert cursor.fetchone()[0] == original_quantity - 1
        cursor.execute(
            """
            SELECT COUNT(*) FROM stock_transactions
             WHERE item_id = %s
               AND transaction_type = 'OUT'
               AND remarks = %s
            """,
            (item_id, "Integration test issue"),
        )
        assert cursor.fetchone()[0] == 1


@pytest.mark.parametrize("quantity", [0, -1])
def test_stock_receipt_rejects_nonpositive_quantity(mysql_connection, quantity):
    with mysql_connection.cursor() as cursor:
        with pytest.raises(mysql.connector.Error):
            cursor.callproc("add_stock", [1, quantity, "Invalid test receipt", "test-user"])


def test_stock_receipt_rejects_unknown_item(mysql_connection):
    with mysql_connection.cursor() as cursor:
        with pytest.raises(mysql.connector.Error):
            cursor.callproc("add_stock", [999999999, 1, "Unknown item", "test-user"])


def test_low_stock_and_slow_moving_reports_include_seed_examples(mysql_connection):
    from app.repositories.inventory import list_low_stock, list_slow_moving

    low_skus = {row["sku"] for row in list_low_stock(mysql_connection)}
    assert {"DEMO-MOU-001", "DEMO-MON-001", "DEMO-USB-001"} <= low_skus
    report_rows = list_slow_moving(mysql_connection, 30)
    statuses_by_sku = {row["sku"]: row["report_status"] for row in report_rows}
    assert statuses_by_sku["DEMO-STN-001"] == "NEVER_ISSUED"


def test_current_stock_report_summary_matches_filtered_mysql_rows(mysql_connection):
    with mysql_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT i.item_id, COALESCE(s.quantity_on_hand, 0), i.reorder_level
              FROM items i
              LEFT JOIN stock s ON s.item_id = i.item_id
             ORDER BY i.item_id
             LIMIT 1
            """
        )
        item = cursor.fetchone()

    assert item is not None
    item_id, quantity, reorder_level = item
    report = list_current_stock_report(
        mysql_connection,
        search=None,
        category=None,
        item_id=int(item_id),
        sort_by="item_name",
        direction="asc",
        limit=10,
        offset=0,
    )

    assert report["total"] == 1
    assert report["summary"] == {
        "total_items": 1,
        "total_units": int(quantity),
        "low_stock_items": int(quantity <= reorder_level),
        "out_of_stock_items": int(quantity == 0),
    }
    assert report["items"][0]["item_id"] == item_id


def test_dashboard_metrics_match_seeded_inventory(mysql_connection):
    summary = dashboard_summary(mysql_connection, 30)

    assert summary["total_unique_items"] == 5
    assert summary["total_units_in_stock"] == 45
    assert summary["low_stock_items"] == 3
    assert summary["out_of_stock_items"] == 1
