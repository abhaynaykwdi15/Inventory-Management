# Inventory Management System

A beginner-friendly inventory application for managing fictional items, current stock, receipts, issues, reorder-level alerts, audit history, and inventory reports.

**Stack:** MySQL 8 · Python FastAPI · React and Vite · Recharts.

The application includes email-verified accounts, secure sign-in/out, profile and password management, password recovery, and a MySQL-backed inventory workspace. Only fictional sample inventory is included. There is no mock-data fallback: when MySQL is unavailable, API requests fail clearly instead of pretending that database writes succeeded.

## Architecture


```text
React dashboard (Vite)
        │ HTTP / JSON (Axios, HttpOnly session cookie)
        ▼
FastAPI routes ── Pydantic validation and account authorization  
        │ MySQL Connector/Python connection pool
        ▼
MySQL sessions, verified users, and inventory tables
        │                              │
        └── stock transaction          └── audit triggers ── audit log
                    │
                    └── API response ──► React refreshes from the server
```

FastAPI accesses MySQL with bound parameters. The `add_stock` and `issue_stock` procedures lock the relevant balance row, update stock, and add a movement record. They do not commit; the API commits on success and rolls back on failure. MySQL triggers record selected item, stock, and transaction changes in `audit_log`. Dashboard metrics and chart datasets come from database-backed API queries, not hard-coded values.

## Project structure

```text
backend/
  app/
    main.py                 FastAPI application and startup
    config.py               Validated environment configuration
    database.py             MySQL connection pool
    schemas/                Pydantic request and response models
    routers/                HTTP endpoint definitions
    services/               Database error translation and transactions
    repositories/            Parameterized MySQL operations
  sql/
    01_schema.sql           Tables, constraints, and indexes
    02_sequences.sql        AUTO_INCREMENT starting values
    03_procedures.sql       Atomic stock operations
    04_triggers.sql         Audit triggers
    05_seed_data.sql        Deterministic fictional records
    06_auth.sql             Account, session, and email-token tables
  tests/                    API unit and optional MySQL integration tests
  requirements.txt
  .env.example
frontend/
  src/                      React pages, components, API client, and styles
  package.json
  .env.example
docs/
  backend-flow.md           Request, transaction, trigger, and refresh flow
  database-design.md        Tables, relationships, procedures, and triggers
CLAUDE_LOG.md                Blank learning-journal template
```

## Prerequisites

- Python 3.12 or 3.13
- Node.js 20 or later
- MySQL Server 8.0 or later
- A current PowerShell terminal on Windows, or equivalent Python/npm commands on another OS

MySQL Server `MySQL80` was found running on this computer at port 3306. SQL scripts and database integration still need to be applied to the local server.

## MySQL database setup

1. Open MySQL Workbench and connect to your local MySQL administrator account. Do not share its password in chat.
2. In a query tab, create the project database and a dedicated local app user. Replace the placeholder with a new password you choose and keep it private:

   ```sql
   CREATE DATABASE IF NOT EXISTS inventory_management
     CHARACTER SET utf8mb4;
   CREATE USER IF NOT EXISTS 'inventory_app'@'localhost'
     IDENTIFIED BY 'choose_a_private_password';
   CREATE USER IF NOT EXISTS 'inventory_app'@'127.0.0.1'
     IDENTIFIED BY 'choose_a_private_password';
   GRANT ALL PRIVILEGES ON inventory_management.*
     TO 'inventory_app'@'localhost';
   GRANT ALL PRIVILEGES ON inventory_management.*
     TO 'inventory_app'@'127.0.0.1';
   ```

   If that app user already exists and you need to set its password, an administrator can run:

   ```sql
   ALTER USER 'inventory_app'@'127.0.0.1'
     IDENTIFIED BY 'choose_a_private_password';
   ALTER USER 'inventory_app'@'localhost'
     IDENTIFIED BY 'choose_a_private_password';
   ```

3. Create a new Workbench connection to `127.0.0.1:3306` as `inventory_app`. Select the `inventory_management` database.
4. Open and run each SQL script in Workbench in this order:

   1. `backend/sql/01_schema.sql`
   2. `backend/sql/02_sequences.sql`
   3. `backend/sql/03_procedures.sql`
   4. `backend/sql/04_triggers.sql`
   5. `backend/sql/05_seed_data.sql`

   The sample script is for an empty database, inserts deterministic fictional records, and is not a reset/re-run script.

5. To add authentication to an existing installation, run `backend/sql/06_auth.sql` once, then rerun `backend/sql/04_triggers.sql` so the audit triggers record the signed-in account. For a fresh installation, run `06_auth.sql` after `05_seed_data.sql`, then rerun `04_triggers.sql`.

## Backend setup

From PowerShell:

```powershell
Set-Location "C:\Users\Abhay Nayakwdi\OneDrive\Desktop\Inventory Management\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` locally with the MySQL app user's credentials. Keep the password private:

```dotenv
INVENTORY_MYSQL_HOST=127.0.0.1
INVENTORY_MYSQL_PORT=3306
INVENTORY_MYSQL_DATABASE=inventory_management
INVENTORY_MYSQL_USER=inventory_app
INVENTORY_MYSQL_PASSWORD=your_private_password
INVENTORY_POOL_SIZE=5
INVENTORY_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
INVENTORY_AUTH_SESSION_HOURS=12
INVENTORY_AUTH_COOKIE_SECURE=false
INVENTORY_AUTH_COOKIE_SAMESITE=lax
INVENTORY_FRONTEND_URL=http://127.0.0.1:5173
INVENTORY_SMTP_HOST=smtp.your-provider.example
INVENTORY_SMTP_PORT=587
INVENTORY_SMTP_USERNAME=your_smtp_username
INVENTORY_SMTP_PASSWORD=your_smtp_password
INVENTORY_SMTP_FROM_EMAIL=inventory@your-domain.example
INVENTORY_SMTP_FROM_NAME=Inventory Desk
INVENTORY_SMTP_STARTTLS=true
INVENTORY_SMTP_USE_SSL=false
```

Set the SMTP values using credentials from your email provider. They remain in `backend/.env`; never place them in the frontend or commit them. SMTP is required for registration verification, email changes, and password reset. The app will not mark an account verified without a valid verification link.

To safely test the configured MySQL login without displaying its password, run this from the backend folder:

```powershell
python -m app.db_check
```

The check performs `SELECT 1`, prints the connection target and result/error code, and exits nonzero if the connection fails.

For production, serve both app and API over HTTPS, set `INVENTORY_AUTH_COOKIE_SECURE=true`, set `INVENTORY_FRONTEND_URL` to the exact public frontend origin, set `INVENTORY_CORS_ORIGINS` to a JSON array containing only that trusted origin, and configure a production SMTP sender. Configure an appropriate `INVENTORY_AUTH_COOKIE_SAMESITE` policy for your deployment domains.

Then start the API in that terminal:

```powershell
python -m uvicorn app.main:app --reload --port 8002
```

The backend reads `backend/.env` regardless of the terminal's current directory. It validates its connection settings, creates a MySQL pool, and ensures the account/session/email-token tables exist at startup. Install the inventory schema with the ordered SQL scripts. If credentials are missing, MySQL cannot be reached, or the account schema cannot be initialized, the API remains available for diagnostics, while database-backed routes return HTTP 503; it never switches to mock data.

## Frontend setup

Open a second terminal:

```powershell
Set-Location "C:\Users\Abhay Nayakwdi\OneDrive\Desktop\Inventory Management\frontend"
npm.cmd install
Copy-Item .env.example .env
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Vite is configured with `strictPort: true`, so it exits rather than switching to another port if 5173 is occupied; stop the conflicting server before starting this frontend. In development, API requests use Vite's same-origin `/api` proxy to `http://127.0.0.1:8002`; this also avoids browser CORS and cross-host cookie issues. For production, the frontend uses `VITE_API_BASE_URL`; never put database or SMTP credentials in the frontend.

## Deploying the frontend to Vercel

The project is deployed and publicly available:

- Frontend: <https://inventory-management-881a.vercel.app>
- Backend health: <https://inventory-management-1-dilf.onrender.com/api/health>
- Source and deployment branch: <https://github.com/abhaynaykwdi15/Inventory-Management> (`main`)

Vercel is connected to the GitHub repository and automatically deploys pushes to `main`. Its project root is `frontend`; `frontend/vercel.json` sends `/api/*` requests through to Render and serves the React entry point for client-side routes. Keep `VITE_API_BASE_URL` unset in Vercel so browser requests and HttpOnly session cookies stay on the frontend origin. The frontend environment example is intentionally blank for the same-origin Vite and Vercel proxies.

Render hosts the FastAPI backend and MySQL database. Keep database and SMTP credentials only in Render's environment settings. Set `INVENTORY_FRONTEND_URL` to `https://inventory-management-881a.vercel.app`, `INVENTORY_AUTH_COOKIE_SECURE=true`, and `INVENTORY_AUTH_COOKIE_SAMESITE=lax`. Configure `INVENTORY_CORS_ORIGINS` with the frontend origin if clients will call the Render API directly; the Vercel same-origin rewrite does not require browser CORS. Configure SMTP to enable verification, password reset, and email-change messages.

The Vercel production deployment must remain public (Vercel Authentication disabled) for visitors who are not signed in to the Vercel team. Do not put database or SMTP credentials in Vercel or frontend environment variables.

## Running tests and checks

Backend unit tests:

```powershell
Set-Location backend
python -m pytest -q
```

MySQL integration tests require the schema and procedures above to be installed in a dedicated test database. Enable them explicitly:

```powershell
$env:INVENTORY_RUN_MYSQL_INTEGRATION = "1"
python -m pytest -q tests/test_mysql_integration.py
```

Do not run integration tests against production. Frontend production build:

```powershell
Set-Location frontend
npm.cmd run build
```

## API endpoints

FastAPI's interactive OpenAPI documentation is available at `http://localhost:8002/docs` when the backend is running.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create an account and send an email-verification link |
| POST | `/api/auth/login` | Sign in and issue an HttpOnly session cookie |
| POST | `/api/auth/logout` | Revoke the current session |
| GET | `/api/auth/me` | Read the signed-in account profile |
| POST | `/api/auth/verify-email` | Verify an email address or confirm an email change |
| POST | `/api/auth/resend-verification` | Resend an account verification email |
| POST | `/api/auth/forgot-password` | Request a password-reset link |
| POST | `/api/auth/reset-password` | Set a new password from a reset link |
| PUT | `/api/auth/profile` | Update a name or request a verified email change |
| DELETE | `/api/auth/profile/pending-email` | Cancel an email change that has not yet been verified |
| POST | `/api/auth/change-password` | Change the signed-in user's password |
| GET | `/api/health` | Check API-to-MySQL connectivity |
| GET | `/api/dashboard/summary?period_days=30` | Summary cards, charts, and recent activity |
| GET | `/api/items` | Search, filter, sort, and paginate items |
| GET | `/api/items/categories` | List categories for filters |
| GET | `/api/items/{item_id}` | Read one item and its current balance |
| POST | `/api/items` | Create an item and its zero-stock row |
| PUT | `/api/items/{item_id}` | Update catalog details |
| DELETE | `/api/items/{item_id}` | Delete only when transaction history is absent |
| GET | `/api/stock` | Read current stock balances |
| GET | `/api/stock/low` | List balances at or below reorder level |
| POST | `/api/stock/in` | Receive stock through `add_stock` |
| POST | `/api/stock/out` | Issue stock through `issue_stock` |
| GET | `/api/transactions` | Filter and paginate transaction history |
| GET | `/api/reports/current-stock` | Filter, sort, paginate, and summarize current stock |
| GET | `/api/reports/current-stock/items` | List item options for the current-stock report filter |
| GET | `/api/reports/slow-moving?days=30` | List never-issued and inactive items |
| GET | `/api/audit-logs` | Read-only paginated audit history |

## Inventory reports

The Reports page includes a **Current stock** report and the existing **Slow-moving stock** report. Current stock data and summary cards are calculated from the MySQL `items` and `stock` tables; the report does not use hard-coded values or substitute mock data. It supports item-name/SKU search, category and exact-item filters, server-side sorting and pagination, and CSV export of all rows matching the active filters. The summary shows matching items, total units, low-stock items, and out-of-stock items. The existing slow-moving report and its inactivity-period filter remain available on a separate report tab.

## Metric and report definitions

- **Unique items** counts catalog rows; it is not a quantity sum.
- **Units in stock** sums current on-hand quantities.
- **Low stock** counts items where on-hand quantity is less than or equal to the reorder level, including zero.
- **Out of stock** counts items whose current quantity is exactly zero.
- **Received/issued in period** sum movement quantities over the selected database-date period.
- **Slow moving** includes items never issued and items whose latest `OUT` transaction is at least the requested number of days old.

## Known limitations

- New accounts are open-registration accounts and all accounts share the same inventory workspace. Role-based access and workspace/tenant separation are not implemented.
- Account endpoints do not replace production deployment controls such as edge rate limiting, monitoring, backups, SMTP deliverability, and HTTPS.
- Audit triggers are useful change history, not a tamper-proof security ledger. Audit snapshots are JSON for display.
- No stock alert email notifications or PDF export are implemented. The report CSV export is implemented.

See [docs/backend-flow.md](docs/backend-flow.md) for transaction behavior, [docs/database-design.md](docs/database-design.md) for SQL details, and [CLAUDE_LOG.md](CLAUDE_LOG.md) for the learning-journal template.
