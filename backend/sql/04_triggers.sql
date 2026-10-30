USE inventory_management;

DROP TRIGGER IF EXISTS trg_items_audit_insert;
DROP TRIGGER IF EXISTS trg_items_audit_update;
DROP TRIGGER IF EXISTS trg_items_audit_delete;
DROP TRIGGER IF EXISTS trg_stock_audit_insert;
DROP TRIGGER IF EXISTS trg_stock_audit_update;
DROP TRIGGER IF EXISTS trg_stock_audit_delete;
DROP TRIGGER IF EXISTS trg_transactions_audit_insert;
DROP TRIGGER IF EXISTS trg_transactions_audit_update;
DROP TRIGGER IF EXISTS trg_transactions_audit_delete;

DELIMITER $$

CREATE TRIGGER trg_items_audit_insert
AFTER INSERT ON items FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, new_value, changed_by)
    VALUES (
        'ITEMS', NEW.item_id, 'INSERT',
        CAST(JSON_OBJECT(
            'item_id', NEW.item_id, 'sku', NEW.sku, 'item_name', NEW.item_name,
            'category', NEW.category, 'description', NEW.description,
            'unit_price', NEW.unit_price, 'reorder_level', NEW.reorder_level,
            'created_at', NEW.created_at, 'updated_at', NEW.updated_at
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_items_audit_update
AFTER UPDATE ON items FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, old_value, new_value, changed_by)
    VALUES (
        'ITEMS', NEW.item_id, 'UPDATE',
        CAST(JSON_OBJECT(
            'item_id', OLD.item_id, 'sku', OLD.sku, 'item_name', OLD.item_name,
            'category', OLD.category, 'description', OLD.description,
            'unit_price', OLD.unit_price, 'reorder_level', OLD.reorder_level,
            'created_at', OLD.created_at, 'updated_at', OLD.updated_at
        ) AS CHAR),
        CAST(JSON_OBJECT(
            'item_id', NEW.item_id, 'sku', NEW.sku, 'item_name', NEW.item_name,
            'category', NEW.category, 'description', NEW.description,
            'unit_price', NEW.unit_price, 'reorder_level', NEW.reorder_level,
            'created_at', NEW.created_at, 'updated_at', NEW.updated_at
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_items_audit_delete
AFTER DELETE ON items FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, old_value, changed_by)
    VALUES (
        'ITEMS', OLD.item_id, 'DELETE',
        CAST(JSON_OBJECT(
            'item_id', OLD.item_id, 'sku', OLD.sku, 'item_name', OLD.item_name,
            'category', OLD.category, 'description', OLD.description,
            'unit_price', OLD.unit_price, 'reorder_level', OLD.reorder_level,
            'created_at', OLD.created_at, 'updated_at', OLD.updated_at
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_stock_audit_insert
AFTER INSERT ON stock FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, new_value, changed_by)
    VALUES (
        'STOCK', NEW.stock_id, 'INSERT',
        CAST(JSON_OBJECT(
            'stock_id', NEW.stock_id, 'item_id', NEW.item_id,
            'quantity_on_hand', NEW.quantity_on_hand, 'updated_at', NEW.updated_at
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_stock_audit_update
AFTER UPDATE ON stock FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, old_value, new_value, changed_by)
    VALUES (
        'STOCK', NEW.stock_id, 'UPDATE',
        CAST(JSON_OBJECT(
            'stock_id', OLD.stock_id, 'item_id', OLD.item_id,
            'quantity_on_hand', OLD.quantity_on_hand, 'updated_at', OLD.updated_at
        ) AS CHAR),
        CAST(JSON_OBJECT(
            'stock_id', NEW.stock_id, 'item_id', NEW.item_id,
            'quantity_on_hand', NEW.quantity_on_hand, 'updated_at', NEW.updated_at
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_stock_audit_delete
AFTER DELETE ON stock FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, old_value, changed_by)
    VALUES (
        'STOCK', OLD.stock_id, 'DELETE',
        CAST(JSON_OBJECT(
            'stock_id', OLD.stock_id, 'item_id', OLD.item_id,
            'quantity_on_hand', OLD.quantity_on_hand, 'updated_at', OLD.updated_at
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_transactions_audit_insert
AFTER INSERT ON stock_transactions FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, new_value, changed_by)
    VALUES (
        'STOCK_TRANSACTIONS', NEW.transaction_id, 'INSERT',
        CAST(JSON_OBJECT(
            'transaction_id', NEW.transaction_id, 'item_id', NEW.item_id,
            'type', NEW.transaction_type, 'quantity', NEW.quantity,
            'transaction_date', NEW.transaction_date, 'remarks', NEW.remarks,
            'reference_number', NEW.reference_number, 'created_by', NEW.created_by
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_transactions_audit_update
AFTER UPDATE ON stock_transactions FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, old_value, new_value, changed_by)
    VALUES (
        'STOCK_TRANSACTIONS', NEW.transaction_id, 'UPDATE',
        CAST(JSON_OBJECT(
            'transaction_id', OLD.transaction_id, 'item_id', OLD.item_id,
            'type', OLD.transaction_type, 'quantity', OLD.quantity,
            'transaction_date', OLD.transaction_date, 'remarks', OLD.remarks,
            'reference_number', OLD.reference_number, 'created_by', OLD.created_by
        ) AS CHAR),
        CAST(JSON_OBJECT(
            'transaction_id', NEW.transaction_id, 'item_id', NEW.item_id,
            'type', NEW.transaction_type, 'quantity', NEW.quantity,
            'transaction_date', NEW.transaction_date, 'remarks', NEW.remarks,
            'reference_number', NEW.reference_number, 'created_by', NEW.created_by
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

CREATE TRIGGER trg_transactions_audit_delete
AFTER DELETE ON stock_transactions FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action_type, old_value, changed_by)
    VALUES (
        'STOCK_TRANSACTIONS', OLD.transaction_id, 'DELETE',
        CAST(JSON_OBJECT(
            'transaction_id', OLD.transaction_id, 'item_id', OLD.item_id,
            'type', OLD.transaction_type, 'quantity', OLD.quantity,
            'transaction_date', OLD.transaction_date, 'remarks', OLD.remarks,
            'reference_number', OLD.reference_number, 'created_by', OLD.created_by
        ) AS CHAR),
        COALESCE(@inventory_actor, USER())
    );
END$$

DELIMITER ;
