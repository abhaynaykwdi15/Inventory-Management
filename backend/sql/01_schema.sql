USE inventory_management;

CREATE TABLE items (
    item_id       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    sku           VARCHAR(40) NOT NULL,
    item_name     VARCHAR(150) NOT NULL,
    category      VARCHAR(80) NOT NULL,
    description   VARCHAR(1000),
    unit_price    DECIMAL(10, 2) NOT NULL DEFAULT 0,
    reorder_level INT UNSIGNED NOT NULL DEFAULT 0,
    created_at    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_items PRIMARY KEY (item_id),
    CONSTRAINT uq_items_sku UNIQUE (sku),
    CONSTRAINT ck_items_price_nonnegative CHECK (unit_price >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=1000 DEFAULT CHARSET=utf8mb4;

CREATE TABLE stock (
    stock_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    item_id          BIGINT UNSIGNED NOT NULL,
    quantity_on_hand BIGINT UNSIGNED NOT NULL DEFAULT 0,
    updated_at       TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_stock PRIMARY KEY (stock_id),
    CONSTRAINT uq_stock_item UNIQUE (item_id),
    CONSTRAINT fk_stock_item FOREIGN KEY (item_id) REFERENCES items (item_id),
    CONSTRAINT ck_stock_quantity_nonnegative CHECK (quantity_on_hand >= 0)
) ENGINE=InnoDB AUTO_INCREMENT=1000 DEFAULT CHARSET=utf8mb4;

CREATE TABLE stock_transactions (
    transaction_id   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    item_id          BIGINT UNSIGNED NOT NULL,
    transaction_type VARCHAR(3) NOT NULL,
    quantity         BIGINT UNSIGNED NOT NULL,
    transaction_date TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    remarks          VARCHAR(500),
    reference_number VARCHAR(100),
    created_by       VARCHAR(254) NOT NULL DEFAULT 'demo-user',
    CONSTRAINT pk_stock_transactions PRIMARY KEY (transaction_id),
    CONSTRAINT fk_transaction_item FOREIGN KEY (item_id) REFERENCES items (item_id),
    CONSTRAINT ck_transaction_type CHECK (transaction_type IN ('IN', 'OUT')),
    CONSTRAINT ck_transaction_quantity_positive CHECK (quantity > 0),
    INDEX ix_transactions_item_date (item_id, transaction_date),
    INDEX ix_transactions_date (transaction_date)
) ENGINE=InnoDB AUTO_INCREMENT=1000 DEFAULT CHARSET=utf8mb4;

CREATE TABLE audit_log (
    audit_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    table_name       VARCHAR(30) NOT NULL,
    record_id        BIGINT UNSIGNED NOT NULL,
    action_type      VARCHAR(6) NOT NULL,
    old_value        LONGTEXT,
    new_value        LONGTEXT,
    changed_by       VARCHAR(288) NOT NULL,
    action_timestamp TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT pk_audit_log PRIMARY KEY (audit_id),
    CONSTRAINT ck_audit_action CHECK (action_type IN ('INSERT', 'UPDATE', 'DELETE')),
    INDEX ix_audit_table_timestamp (table_name, action_timestamp)
) ENGINE=InnoDB AUTO_INCREMENT=1000 DEFAULT CHARSET=utf8mb4;
