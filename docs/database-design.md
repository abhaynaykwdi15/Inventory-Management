# Database design

The MySQL schema separates an item's catalog details, its current balance, its movement history, and its audit history. All sample records are fictional.

## Tables and relationships

- **ITEMS** stores one catalog row per SKU. The SKU is unique; prices and reorder levels cannot be negative.
- **STOCK** stores one current balance per item. Its unique foreign key means each item has at most one balance row, and a check constraint prevents negative quantities.
- **STOCK_TRANSACTIONS** stores each receipt (`IN`) or issue (`OUT`) as an immutable movement row. The item is a foreign key, the type is restricted to `IN`/`OUT`, and quantity must be positive.
- **AUDIT_LOG** stores selected row changes from audited tables. JSON snapshots are stored as `LONGTEXT`. It has no foreign key to the audited row because a deletion must remain auditable after that row is gone.
- **APP_USERS** stores account names, unique email addresses, a pending email change, an email-verification state, and a salted password hash. Plaintext passwords are never stored.
- **USER_SESSIONS** stores only a SHA-256 hash of each random, expiring session token; the browser receives the opaque token only in an HttpOnly cookie.
- **ACCOUNT_TOKENS** stores hashed, single-use, 30-minute verification, email-change, and password-reset tokens.

All tables use InnoDB for transactional writes, row locks, and foreign-key enforcement. The relationships are `ITEMS 1 ─ 0..1 STOCK` and `ITEMS 1 ─ many STOCK_TRANSACTIONS`. Audit rows are associated by table name and record ID rather than a foreign key.

## Primary keys

MySQL `AUTO_INCREMENT` columns generate application IDs. Tables begin at 1000 so fixed sample rows (IDs 1 through 8) are easy to distinguish. The next values are not transactional, so gaps after rolled-back operations are expected and harmless.

## Execution order

Create the database and dedicated application user first. Then run these scripts as `inventory_app` in order:

1. `01_schema.sql`
2. `02_sequences.sql` (sets `AUTO_INCREMENT` starting values; MySQL does not use sequences here)
3. `03_procedures.sql`
4. `04_triggers.sql`
5. `05_seed_data.sql`
6. `06_auth.sql`

For an existing installation, run `06_auth.sql` once and rerun `04_triggers.sql` to install the triggers that attribute inventory changes to the authenticated email.

The seed script is intended for a new, empty database and is not idempotent.

## Demo-data balance

The starting quantity reflects the included movement history: Keyboard 25 received and 5 issued leaves 20; Mouse 20 received and 12 issued leaves 8; Monitor 5 received and 2 issued leaves 3; USB Cable 30 received and 30 issued leaves 0; Laptop Stand starts at 14 and has never been issued. Mouse, Monitor, and USB Cable are at or below their reorder levels.

The fixed transaction timestamps make seed data deterministic. Slow-moving report comparisons use MySQL's current date, so the example activity ages naturally.

## Stock procedures and reports

- `add_stock` and `issue_stock` reject missing IDs and non-positive or fractional quantities, validate the item and balance row, lock that balance with `SELECT ... FOR UPDATE`, update stock, and insert an `IN` or `OUT` movement. They deliberately do not commit; the API owns the transaction boundary. `issue_stock` signals an error if stock is insufficient.
- Low-stock and slow-moving reports are parameterized repository queries. Low stock includes balances at or below reorder level. Slow moving includes never-issued items and items whose latest `OUT` transaction is at least the requested number of days old, with `NEVER_ISSUED` distinguished from `INACTIVE`.
- Duplicate SKU and stock procedure errors are translated to safe HTTP responses. Other database failures are rolled back and returned without leaking driver details.

## Audit triggers

Three insert/update/delete triggers each for `items`, `stock`, and `stock_transactions` record table name, record ID, action, JSON old/new snapshots where applicable, authenticated account email (falling back to the MySQL session user for non-application changes), and database timestamp in `audit_log`. The API assigns the actor to its checked-out database connection for the request; MySQL's pool session reset clears it before that connection is reused. Stock movement `created_by` is assigned by the backend from the verified account, never trusted from the request body. Because trigger writes participate in the same InnoDB transaction, an audit insert failure also fails the underlying change.

The snapshots are for display and are not a tamper-proof security ledger. Accounts currently share one inventory workspace; tenant isolation and role-based permissions are not implemented.
