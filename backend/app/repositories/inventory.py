from datetime import date
from typing import Any, Literal

from app.services.database_errors import InventoryConflict, ResourceNotFound


def _rows(cursor: Any) -> list[dict[str, Any]]:
    names = [column[0].lower() for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def _row(cursor: Any) -> dict[str, Any] | None:
    names = [column[0].lower() for column in cursor.description]
    values = cursor.fetchone()
    return dict(zip(names, values)) if values is not None else None


def health_check(connection: Any) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()


def dashboard_summary(connection: Any, period_days: int) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(i.item_id) AS total_unique_items,
                   COALESCE(SUM(COALESCE(s.quantity_on_hand, 0)), 0) AS total_units_in_stock,
                   COALESCE(SUM(
                       CASE WHEN COALESCE(s.quantity_on_hand, 0) <= i.reorder_level
                            THEN 1 ELSE 0 END
                   ), 0) AS low_stock_items,
                   COALESCE(SUM(
                       CASE WHEN COALESCE(s.quantity_on_hand, 0) = 0
                            THEN 1 ELSE 0 END
                   ), 0) AS out_of_stock_items
              FROM items i
              LEFT JOIN stock s ON s.item_id = i.item_id
            """
        )
        summary = _row(cursor)
        assert summary is not None
        cursor.execute(
            """
            SELECT COALESCE(SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE 0 END), 0)
                       AS stock_received_in_period,
                   COALESCE(SUM(CASE WHEN transaction_type = 'OUT' THEN quantity ELSE 0 END), 0)
                       AS stock_issued_in_period
              FROM stock_transactions
             WHERE transaction_date >= DATE_SUB(
                   CURRENT_TIMESTAMP, INTERVAL %(period_days)s DAY
             )
            """,
            {"period_days": period_days},
        )
        period_metrics = _row(cursor)
        assert period_metrics is not None
        summary.update(period_metrics)
        cursor.execute(
            """
            SELECT i.category, SUM(s.quantity_on_hand) AS quantity_on_hand
              FROM items i
              JOIN stock s ON s.item_id = i.item_id
             GROUP BY i.category
             ORDER BY i.category
            """
        )
        stock_by_category = _rows(cursor)
        cursor.execute(
            """
            SELECT DATE(transaction_date) AS transaction_day,
                   SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE 0 END) AS stock_in,
                   SUM(CASE WHEN transaction_type = 'OUT' THEN quantity ELSE 0 END) AS stock_out
              FROM stock_transactions
             WHERE transaction_date >= DATE_SUB(
                   CURRENT_TIMESTAMP, INTERVAL %(period_days)s DAY
             )
             GROUP BY DATE(transaction_date)
             ORDER BY transaction_day
            """,
            {"period_days": period_days},
        )
        movement_by_day = _rows(cursor)

    summary["period_days"] = period_days
    summary["stock_by_category"] = stock_by_category
    summary["movement_by_day"] = movement_by_day
    summary["low_stock_comparison"] = list_low_stock(connection)
    recent = list_transactions(
        connection,
        transaction_type=None,
        item_id=None,
        date_from=None,
        date_to=None,
        limit=8,
        offset=0,
    )
    summary["recent_transactions"] = recent["items"]
    return summary


def list_items(
    connection: Any,
    *,
    search: str | None,
    category: str | None,
    sort_by: str,
    direction: str,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    sort_columns = {
        "item_name": "i.item_name",
        "sku": "i.sku",
        "category": "i.category",
        "unit_price": "i.unit_price",
        "quantity_on_hand": "COALESCE(s.quantity_on_hand, 0)",
    }
    where_parts: list[str] = []
    binds: dict[str, Any] = {}
    if search:
        where_parts.append(
            "(LOCATE(LOWER(%(search)s), LOWER(i.item_name)) > 0 "
            "OR LOCATE(LOWER(%(search)s), LOWER(i.sku)) > 0)"
        )
        binds["search"] = search
    if category:
        where_parts.append("i.category = %(category)s")
        binds["category"] = category
    where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""
    order_column = sort_columns[sort_by]
    order_direction = "DESC" if direction == "desc" else "ASC"
    count_binds = dict(binds)
    binds.update({"limit": limit, "offset": offset})

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM items i LEFT JOIN stock s ON s.item_id = i.item_id"
            + where_clause,
            count_binds,
        )
        total = int(cursor.fetchone()[0])
        cursor.execute(
            f"""
            SELECT i.item_id, i.sku, i.item_name, i.category, i.description,
                   i.unit_price, i.reorder_level,
                   COALESCE(s.quantity_on_hand, 0) AS quantity_on_hand,
                   i.created_at, i.updated_at
              FROM items i
              LEFT JOIN stock s ON s.item_id = i.item_id
              {where_clause}
             ORDER BY {order_column} {order_direction}, i.item_id ASC
             LIMIT %(limit)s OFFSET %(offset)s
            """,
            binds,
        )
        return {"items": _rows(cursor), "total": total, "limit": limit, "offset": offset}


def get_item(connection: Any, item_id: int) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT i.item_id, i.sku, i.item_name, i.category, i.description,
                   i.unit_price, i.reorder_level,
                   COALESCE(s.quantity_on_hand, 0) AS quantity_on_hand,
                   i.created_at, i.updated_at
              FROM items i
              LEFT JOIN stock s ON s.item_id = i.item_id
             WHERE i.item_id = %(item_id)s
            """,
            {"item_id": item_id},
        )
        item = _row(cursor)
    if item is None:
        raise ResourceNotFound("Item not found.")
    return item


def list_item_categories(connection: Any) -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT category FROM items ORDER BY category")
        return [row[0] for row in cursor.fetchall()]


def list_current_stock_item_options(
    connection: Any,
    category: str | None,
) -> list[dict[str, Any]]:
    binds: dict[str, Any] = {}
    where_clause = ""
    if category:
        where_clause = "WHERE category = %(category)s"
        binds["category"] = category
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT item_id, item_name, sku, category
              FROM items
              {where_clause}
             ORDER BY item_name, item_id
            """,
            binds,
        )
        return _rows(cursor)


def list_current_stock_report(
    connection: Any,
    *,
    search: str | None,
    category: str | None,
    item_id: int | None,
    sort_by: str,
    direction: str,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    sort_columns = {
        "item_name": "i.item_name",
        "sku": "i.sku",
        "category": "i.category",
        "quantity_on_hand": "COALESCE(s.quantity_on_hand, 0)",
        "reorder_level": "i.reorder_level",
        "updated_at": "s.updated_at",
    }
    where_parts: list[str] = []
    binds: dict[str, Any] = {}
    if search:
        where_parts.append(
            "(LOCATE(LOWER(%(search)s), LOWER(i.item_name)) > 0 "
            "OR LOCATE(LOWER(%(search)s), LOWER(i.sku)) > 0)"
        )
        binds["search"] = search
    if category:
        where_parts.append("i.category = %(category)s")
        binds["category"] = category
    if item_id is not None:
        where_parts.append("i.item_id = %(item_id)s")
        binds["item_id"] = item_id
    where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""
    order_column = sort_columns[sort_by]
    order_direction = "DESC" if direction == "desc" else "ASC"
    count_binds = dict(binds)
    binds.update({"limit": limit, "offset": offset})

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(i.item_id) AS total_items,
                   COALESCE(SUM(COALESCE(s.quantity_on_hand, 0)), 0) AS total_units,
                   COALESCE(SUM(
                       CASE WHEN COALESCE(s.quantity_on_hand, 0) <= i.reorder_level
                            THEN 1 ELSE 0 END
                   ), 0) AS low_stock_items,
                   COALESCE(SUM(
                       CASE WHEN COALESCE(s.quantity_on_hand, 0) = 0
                            THEN 1 ELSE 0 END
                   ), 0) AS out_of_stock_items
              FROM items i
              LEFT JOIN stock s ON s.item_id = i.item_id
              {where_clause}
            """,
            count_binds,
        )
        summary = _row(cursor)
        assert summary is not None
        cursor.execute(
            f"""
            SELECT i.item_id, i.sku, i.item_name, i.category,
                   COALESCE(s.quantity_on_hand, 0) AS quantity_on_hand,
                   i.reorder_level, s.updated_at
              FROM items i
              LEFT JOIN stock s ON s.item_id = i.item_id
              {where_clause}
             ORDER BY {order_column} {order_direction}, i.item_id ASC
             LIMIT %(limit)s OFFSET %(offset)s
            """,
            binds,
        )
        return {
            "items": _rows(cursor),
            "total": int(summary["total_items"]),
            "limit": limit,
            "offset": offset,
            "summary": {
                key: int(summary[key])
                for key in (
                    "total_items",
                    "total_units",
                    "low_stock_items",
                    "out_of_stock_items",
                )
            },
        }


def create_item(connection: Any, item: dict[str, Any]) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO items (
                sku, item_name, category, description, unit_price, reorder_level
            ) VALUES (
                %(sku)s, %(item_name)s, %(category)s, %(description)s,
                %(unit_price)s, %(reorder_level)s
            )
            """,
            item,
        )
        new_id = int(cursor.lastrowid)
        cursor.execute(
            """
            INSERT INTO stock (item_id, quantity_on_hand)
            VALUES (%(item_id)s, 0)
            """,
            {"item_id": new_id},
        )
    return get_item(connection, new_id)


def update_item(connection: Any, item_id: int, item: dict[str, Any]) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE items
               SET sku = %(sku)s,
                   item_name = %(item_name)s,
                   category = %(category)s,
                   description = %(description)s,
                   unit_price = %(unit_price)s,
                   reorder_level = %(reorder_level)s,
                   updated_at = CURRENT_TIMESTAMP(3)
             WHERE item_id = %(item_id)s
            """,
            {**item, "item_id": item_id},
        )
    return get_item(connection, item_id)


def delete_item(connection: Any, item_id: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM stock_transactions WHERE item_id = %(item_id)s",
            {"item_id": item_id},
        )
        if int(cursor.fetchone()[0]) > 0:
            raise InventoryConflict("An item with transaction history cannot be deleted.")
        cursor.execute("DELETE FROM stock WHERE item_id = %(item_id)s", {"item_id": item_id})
        cursor.execute("DELETE FROM items WHERE item_id = %(item_id)s", {"item_id": item_id})
        if cursor.rowcount == 0:
            raise ResourceNotFound("Item not found.")


def list_stock(connection: Any) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.stock_id, i.item_id, i.sku, i.item_name, i.category,
                   s.quantity_on_hand, i.reorder_level, s.updated_at
              FROM stock s
              JOIN items i ON i.item_id = s.item_id
             ORDER BY i.item_name
            """
        )
        return _rows(cursor)


def list_low_stock(connection: Any) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT i.item_id, i.sku, i.item_name, i.category,
                   s.quantity_on_hand, i.reorder_level,
                   GREATEST(i.reorder_level - s.quantity_on_hand, 0) AS shortage_quantity
              FROM items i
              JOIN stock s ON s.item_id = i.item_id
             WHERE s.quantity_on_hand <= i.reorder_level
             ORDER BY s.quantity_on_hand ASC, i.item_name ASC
            """
        )
        return _rows(cursor)


def _stock_movement(
    connection: Any,
    *,
    procedure_name: Literal["add_stock", "issue_stock"],
    item_id: int,
    quantity: int,
    remarks: str | None,
    created_by: str,
) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.callproc(procedure_name, [item_id, quantity, remarks, created_by])
    result = get_item(connection, item_id)
    return {
        "item_id": item_id,
        "quantity_on_hand": result["quantity_on_hand"],
        "message": "Stock received successfully." if procedure_name == "add_stock"
        else "Stock issued successfully.",
    }


def add_stock(
    connection: Any, *, item_id: int, quantity: int, remarks: str | None, created_by: str
) -> dict[str, Any]:
    return _stock_movement(
        connection,
        procedure_name="add_stock",
        item_id=item_id,
        quantity=quantity,
        remarks=remarks,
        created_by=created_by,
    )


def issue_stock(
    connection: Any, *, item_id: int, quantity: int, remarks: str | None, created_by: str
) -> dict[str, Any]:
    return _stock_movement(
        connection,
        procedure_name="issue_stock",
        item_id=item_id,
        quantity=quantity,
        remarks=remarks,
        created_by=created_by,
    )


def list_transactions(
    connection: Any,
    *,
    transaction_type: str | None,
    item_id: int | None,
    date_from: date | None,
    date_to: date | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    where_parts: list[str] = []
    binds: dict[str, Any] = {}
    if transaction_type:
        where_parts.append("t.transaction_type = %(transaction_type)s")
        binds["transaction_type"] = transaction_type
    if item_id is not None:
        where_parts.append("t.item_id = %(item_id)s")
        binds["item_id"] = item_id
    if date_from:
        where_parts.append("t.transaction_date >= %(date_from)s")
        binds["date_from"] = date_from
    if date_to:
        where_parts.append("t.transaction_date < DATE_ADD(%(date_to)s, INTERVAL 1 DAY)")
        binds["date_to"] = date_to
    where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""
    query_binds = {**binds, "limit": limit, "offset": offset}
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM stock_transactions t" + where_clause,
            binds,
        )
        total = int(cursor.fetchone()[0])
        cursor.execute(
            f"""
            SELECT t.transaction_id, t.item_id, i.sku, i.item_name,
                   t.transaction_type, t.quantity, t.transaction_date,
                   t.remarks, t.reference_number, t.created_by
              FROM stock_transactions t
              JOIN items i ON i.item_id = t.item_id
              {where_clause}
             ORDER BY t.transaction_date DESC, t.transaction_id DESC
             LIMIT %(limit)s OFFSET %(offset)s
            """,
            query_binds,
        )
        return {"items": _rows(cursor), "total": total, "limit": limit, "offset": offset}


def list_slow_moving(connection: Any, days: int) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH last_issues AS (
                SELECT item_id, MAX(transaction_date) AS last_issue_date
                  FROM stock_transactions
                 WHERE transaction_type = 'OUT'
                 GROUP BY item_id
            )
            SELECT i.item_id, i.sku, i.item_name, i.category,
                   s.quantity_on_hand, li.last_issue_date,
                   CASE
                       WHEN li.last_issue_date IS NULL THEN NULL
                       ELSE DATEDIFF(CURRENT_DATE, DATE(li.last_issue_date))
                   END AS days_since_last_issue,
                   CASE
                       WHEN li.last_issue_date IS NULL THEN 'NEVER_ISSUED'
                       ELSE 'INACTIVE'
                   END AS report_status
              FROM items i
              JOIN stock s ON s.item_id = i.item_id
              LEFT JOIN last_issues li ON li.item_id = i.item_id
             WHERE li.last_issue_date IS NULL
                OR li.last_issue_date <= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL %(days)s DAY)
             ORDER BY (li.last_issue_date IS NOT NULL),
                      li.last_issue_date ASC,
                      i.item_name ASC
            """,
            {"days": days},
        )
        return _rows(cursor)


def list_audit_logs(
    connection: Any,
    *,
    table_name: str | None,
    action_type: str | None,
    search: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    where_parts: list[str] = []
    binds: dict[str, Any] = {}
    if table_name:
        where_parts.append("table_name = %(table_name)s")
        binds["table_name"] = table_name.upper()
    if action_type:
        where_parts.append("action_type = %(action_type)s")
        binds["action_type"] = action_type.upper()
    if search:
        where_parts.append(
            "(LOCATE(LOWER(%(search)s), LOWER(table_name)) > 0 "
            "OR LOCATE(LOWER(%(search)s), LOWER(COALESCE(old_value, ''))) > 0 "
            "OR LOCATE(LOWER(%(search)s), LOWER(COALESCE(new_value, ''))) > 0 "
            "OR LOCATE(LOWER(%(search)s), LOWER(changed_by)) > 0)"
        )
        binds["search"] = search
    where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""
    query_binds = {**binds, "limit": limit, "offset": offset}
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM audit_log" + where_clause, binds)
        total = int(cursor.fetchone()[0])
        cursor.execute(
            f"""
            SELECT audit_id, table_name, record_id, action_type, old_value,
                   new_value, changed_by, action_timestamp
              FROM audit_log
              {where_clause}
             ORDER BY action_timestamp DESC, audit_id DESC
             LIMIT %(limit)s OFFSET %(offset)s
            """,
            query_binds,
        )
        return {"items": _rows(cursor), "total": total, "limit": limit, "offset": offset}
