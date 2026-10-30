USE inventory_management;

DROP PROCEDURE IF EXISTS add_stock;
DROP PROCEDURE IF EXISTS issue_stock;

DELIMITER $$

CREATE PROCEDURE add_stock(
    IN p_item_id BIGINT,
    IN p_quantity DECIMAL(20, 4),
    IN p_remarks VARCHAR(500),
    IN p_created_by VARCHAR(128)
)
BEGIN
    DECLARE v_quantity_on_hand BIGINT UNSIGNED;

    IF p_item_id IS NULL OR p_item_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644, MESSAGE_TEXT = 'Item ID is required.';
    END IF;
    IF p_quantity IS NULL OR p_quantity <= 0 OR p_quantity <> TRUNCATE(p_quantity, 0) THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644,
            MESSAGE_TEXT = 'Quantity must be a positive whole number.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM items WHERE item_id = p_item_id) THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644, MESSAGE_TEXT = 'Item does not exist.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM stock WHERE item_id = p_item_id) THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644,
            MESSAGE_TEXT = 'Stock record does not exist for this item.';
    END IF;

    SELECT quantity_on_hand
      INTO v_quantity_on_hand
      FROM stock
     WHERE item_id = p_item_id
       FOR UPDATE;

    UPDATE stock
       SET quantity_on_hand = v_quantity_on_hand + p_quantity,
           updated_at = CURRENT_TIMESTAMP(3)
     WHERE item_id = p_item_id;

    INSERT INTO stock_transactions (
        item_id, transaction_type, quantity, transaction_date, remarks, created_by
    ) VALUES (
        p_item_id, 'IN', p_quantity, CURRENT_TIMESTAMP(3), p_remarks,
        COALESCE(NULLIF(TRIM(p_created_by), ''), USER())
    );
END$$

CREATE PROCEDURE issue_stock(
    IN p_item_id BIGINT,
    IN p_quantity DECIMAL(20, 4),
    IN p_remarks VARCHAR(500),
    IN p_created_by VARCHAR(128)
)
BEGIN
    DECLARE v_quantity_on_hand BIGINT UNSIGNED;

    IF p_item_id IS NULL OR p_item_id <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644, MESSAGE_TEXT = 'Item ID is required.';
    END IF;
    IF p_quantity IS NULL OR p_quantity <= 0 OR p_quantity <> TRUNCATE(p_quantity, 0) THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644,
            MESSAGE_TEXT = 'Quantity must be a positive whole number.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM items WHERE item_id = p_item_id) THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644, MESSAGE_TEXT = 'Item does not exist.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM stock WHERE item_id = p_item_id) THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644,
            MESSAGE_TEXT = 'Stock record does not exist for this item.';
    END IF;

    SELECT quantity_on_hand
      INTO v_quantity_on_hand
      FROM stock
     WHERE item_id = p_item_id
       FOR UPDATE;

    IF v_quantity_on_hand < p_quantity THEN
        SIGNAL SQLSTATE '45000' SET MYSQL_ERRNO = 1644,
            MESSAGE_TEXT = 'Insufficient stock for this issue.';
    END IF;

    UPDATE stock
       SET quantity_on_hand = v_quantity_on_hand - p_quantity,
           updated_at = CURRENT_TIMESTAMP(3)
     WHERE item_id = p_item_id;

    INSERT INTO stock_transactions (
        item_id, transaction_type, quantity, transaction_date, remarks, created_by
    ) VALUES (
        p_item_id, 'OUT', p_quantity, CURRENT_TIMESTAMP(3), p_remarks,
        COALESCE(NULLIF(TRIM(p_created_by), ''), USER())
    );
END$$

DELIMITER ;
