# Backend request flow

This document describes the MySQL-backed request path for stock operations and dashboard reads.

```text
React dashboard
    │ POST /api/stock/in or /api/stock/out
    ▼
FastAPI route
    │ Validate request and HttpOnly session cookie
    ▼
Application service / MySQL repository
    │ Bind values as parameters; set verified actor; invoke a procedure
    ▼
MySQL stock procedure
    ├── Lock and validate the relevant stock row
    ├── Update the stock balance
    └── Insert the matching stock transaction
             │
             ▼
        InnoDB tables
             │ row changes fire audit triggers
             ▼
         Audit log
             │ API commits on success or rolls back on failure
             ▼
FastAPI response ──► React refreshes server data
```

Dashboard charts and summary cards call `GET /api/dashboard/summary`. MySQL computes item counts, unit totals, low/out-of-stock counts, period receipt/issue quantities, category totals, movement-by-day rows, low-stock comparisons, and recent activity. The endpoint does not derive totals from a limited transaction page, and the frontend shows an empty state when chart datasets contain no rows.

## Account and session flow

Registration creates an unverified account and emails a one-time verification link. Passwords are salted and hashed by the backend; email action links are also stored only as token hashes and expire after 30 minutes. Successful sign-in creates a random server-side session whose hash is stored in MySQL and whose opaque value is returned only in an HttpOnly cookie. Inventory and account-management routes require that session. Sign-out revokes it; password reset revokes all of the account's sessions, and password change revokes other sessions.

Verification, password reset, and email-change messages require SMTP settings in `backend/.env`. The frontend receives neither SMTP credentials nor password/session tokens in local storage.

## Atomic stock changes

A stock receipt or issue changes the current balance and transaction history together. The stored procedure locks the balance row with `SELECT ... FOR UPDATE`; if the procedure or audit trigger fails, the API rolls back the request so the balance and movement record remain consistent. Stock issues cannot exceed the available balance, including when concurrent requests arrive.

The procedures do not commit independently. The API owns the transaction boundary and commits only after the stored procedure and follow-up query succeed.

## Audit behavior

MySQL row triggers run after insert, update, or delete operations on items, stock, and stock transactions. They record JSON snapshots and the verified account email for application requests (falling back to the database session user otherwise) in `audit_log`. The audit-log table is not audited by these triggers, avoiding recursive writes. The frontend exposes audit history as read-only.

Triggers record database changes, not the full user intent or an entire API request. Database administrators with sufficient privileges may also alter audit data; triggers alone are not tamper-proof auditing.

## Error handling

Request validation errors are returned as client errors. MySQL failures trigger rollback and a safe API error response; internal connection details, SQL text, and credentials are not exposed to the browser. A successful UI update follows a successful API response and refreshes from the server rather than relying on an optimistic stock change.
