USE inventory_management;

-- Fictional demonstration data. IDs and values are fixed for repeatable
-- reports and tests. Run this script once in an empty database.

INSERT INTO items (
    item_id, sku, item_name, category, description, unit_price, reorder_level
) VALUES (
    1, 'DEMO-KBD-001', 'Keyboard', 'Peripherals',
    'Fictional wired keyboard for demonstration.', 29.99, 10
);

INSERT INTO items (
    item_id, sku, item_name, category, description, unit_price, reorder_level
) VALUES (
    2, 'DEMO-MOU-001', 'Mouse', 'Peripherals',
    'Fictional optical mouse for demonstration.', 14.50, 10
);

INSERT INTO items (
    item_id, sku, item_name, category, description, unit_price, reorder_level
) VALUES (
    3, 'DEMO-MON-001', 'Monitor', 'Displays',
    'Fictional 24-inch monitor for demonstration.', 159.00, 5
);

INSERT INTO items (
    item_id, sku, item_name, category, description, unit_price, reorder_level
) VALUES (
    4, 'DEMO-USB-001', 'USB Cable', 'Accessories',
    'Fictional USB cable for demonstration.', 5.25, 10
);

INSERT INTO items (
    item_id, sku, item_name, category, description, unit_price, reorder_level
) VALUES (
    5, 'DEMO-STN-001', 'Laptop Stand', 'Accessories',
    'Fictional adjustable laptop stand for demonstration.', 34.75, 6
);

INSERT INTO stock (stock_id, item_id, quantity_on_hand) VALUES (1, 1, 20);
INSERT INTO stock (stock_id, item_id, quantity_on_hand) VALUES (2, 2, 8);
INSERT INTO stock (stock_id, item_id, quantity_on_hand) VALUES (3, 3, 3);
INSERT INTO stock (stock_id, item_id, quantity_on_hand) VALUES (4, 4, 0);
INSERT INTO stock (stock_id, item_id, quantity_on_hand) VALUES (5, 5, 14);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    1, 1, 'IN', 25, '2026-09-01 09:00:00',
    'Fictional opening stock', 'DEMO-RECEIPT-001', 'demo-user'
);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    2, 1, 'OUT', 5, '2026-10-20 10:30:00',
    'Fictional demonstration issue', 'DEMO-ISSUE-001', 'demo-user'
);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    3, 2, 'IN', 20, '2026-08-15 09:00:00',
    'Fictional opening stock', 'DEMO-RECEIPT-002', 'demo-user'
);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    4, 2, 'OUT', 12, '2026-09-10 14:15:00',
    'Fictional demonstration issue', 'DEMO-ISSUE-002', 'demo-user'
);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    5, 3, 'IN', 5, '2026-07-01 11:00:00',
    'Fictional opening stock', 'DEMO-RECEIPT-003', 'demo-user'
);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    6, 3, 'OUT', 2, '2026-07-12 16:45:00',
    'Fictional demonstration issue', 'DEMO-ISSUE-003', 'demo-user'
);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    7, 4, 'IN', 30, '2026-06-10 08:00:00',
    'Fictional opening stock', 'DEMO-RECEIPT-004', 'demo-user'
);

INSERT INTO stock_transactions (
    transaction_id, item_id, transaction_type, quantity, transaction_date,
    remarks, reference_number, created_by
) VALUES (
    8, 4, 'OUT', 30, '2026-08-01 13:20:00',
    'Fictional demonstration issue', 'DEMO-ISSUE-004', 'demo-user'
);

COMMIT;
