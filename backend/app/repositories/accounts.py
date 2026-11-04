
from datetime import datetime
from typing import Any

from app.services.auth_security import hash_token


def _account(cursor: Any) -> dict[str, Any] | None:
    row = cursor.fetchone()
    if row is None:
        return None
    names = [column[0].lower() for column in cursor.description]
    return dict(zip(names, row))


def create_account(
    connection: Any,
    *,
    full_name: str,
    email: str,
    password_hash: str,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO app_users (
                full_name, email, password_hash, email_verified
            )
            VALUES (
                %(full_name)s, %(email)s, %(password_hash)s, TRUE
            )
            """,
            {
                "full_name": full_name,
                "email": email,
                "password_hash": password_hash,
            },
        )
        return int(cursor.lastrowid)


def get_account_by_email(
    connection: Any,
    email: str,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, email, pending_email,
                   password_hash, email_verified
              FROM app_users
             WHERE email = %(email)s
            """,
            {"email": email},
        )
        return _account(cursor)


def email_is_unavailable(
    connection: Any,
    email: str,
    exclude_user_id: int | None = None,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
              FROM app_users
             WHERE (email = %(email)s OR pending_email = %(email)s)
               AND (
                    %(exclude_user_id)s IS NULL
                    OR user_id <> %(exclude_user_id)s
               )
             LIMIT 1
            """,
            {
                "email": email,
                "exclude_user_id": exclude_user_id,
            },
        )
        return cursor.fetchone() is not None


def get_account_by_id(
    connection: Any,
    user_id: int,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, email, pending_email, email_verified
              FROM app_users
             WHERE user_id = %(user_id)s
            """,
            {"user_id": user_id},
        )
        return _account(cursor)


# Legacy token functions retained temporarily until auth.py is updated.

def create_email_token(
    connection: Any,
    *,
    user_id: int,
    token: str,
    purpose: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM account_tokens
             WHERE user_id = %(user_id)s AND purpose = %(purpose)s
            """,
            {"user_id": user_id, "purpose": purpose},
        )
        cursor.execute(
            """
            INSERT INTO account_tokens (user_id, token_hash, purpose, expires_at)
            VALUES (
                %(user_id)s, %(token_hash)s, %(purpose)s,
                DATE_ADD(UTC_TIMESTAMP(), INTERVAL 30 MINUTE)
            )
            """,
            {
                "user_id": user_id,
                "token_hash": hash_token(token),
                "purpose": purpose,
            },
        )


def verify_email_token(connection: Any, token: str) -> bool:
    return (
        _consume_email_token(connection, token, "verify_email")
        or _consume_email_token(connection, token, "change_email")
    )


def _consume_email_token(
    connection: Any,
    token: str,
    purpose: str,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id
              FROM account_tokens
             WHERE token_hash = %(token_hash)s
               AND purpose = %(purpose)s
               AND expires_at > UTC_TIMESTAMP()
             FOR UPDATE
            """,
            {
                "token_hash": hash_token(token),
                "purpose": purpose,
            },
        )
        row = cursor.fetchone()
        if row is None:
            return False

        user_id = int(row[0])

        if purpose == "verify_email":
            cursor.execute(
                """
                UPDATE app_users
                   SET email_verified = TRUE
                 WHERE user_id = %(user_id)s
                """,
                {"user_id": user_id},
            )
        else:
            cursor.execute(
                """
                UPDATE app_users
                   SET email = pending_email, pending_email = NULL
                 WHERE user_id = %(user_id)s
                   AND pending_email IS NOT NULL
                """,
                {"user_id": user_id},
            )
            if cursor.rowcount != 1:
                return False

        cursor.execute(
            """
            DELETE FROM account_tokens
             WHERE token_hash = %(token_hash)s
            """,
            {"token_hash": hash_token(token)},
        )
        return True


def create_session(
    connection: Any,
    *,
    user_id: int,
    token: str,
    expires_at: datetime,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO user_sessions (user_id, token_hash, expires_at)
            VALUES (%(user_id)s, %(token_hash)s, %(expires_at)s)
            """,
            {
                "user_id": user_id,
                "token_hash": hash_token(token),
                "expires_at": expires_at,
            },
        )


def get_session_account(
    connection: Any,
    token: str,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.email, u.pending_email,
                   u.email_verified
              FROM user_sessions s
              JOIN app_users u ON u.user_id = s.user_id
             WHERE s.token_hash = %(token_hash)s
               AND s.expires_at > UTC_TIMESTAMP()
            """,
            {"token_hash": hash_token(token)},
        )
        return _account(cursor)


def delete_session(connection: Any, token: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM user_sessions
             WHERE token_hash = %(token_hash)s
            """,
            {"token_hash": hash_token(token)},
        )


def set_pending_email(
    connection: Any,
    user_id: int,
    email: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE app_users
               SET pending_email = %(email)s
             WHERE user_id = %(user_id)s
            """,
            {"email": email, "user_id": user_id},
        )


def cancel_pending_email(connection: Any, user_id: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE app_users
               SET pending_email = NULL
             WHERE user_id = %(user_id)s
            """,
            {"user_id": user_id},
        )
        cursor.execute(
            """
            DELETE FROM account_tokens
             WHERE user_id = %(user_id)s
               AND purpose = 'change_email'
            """,
            {"user_id": user_id},
        )


def password_hash_for_user(
    connection: Any,
    user_id: int,
) -> str | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT password_hash
              FROM app_users
             WHERE user_id = %(user_id)s
            """,
            {"user_id": user_id},
        )
        row = cursor.fetchone()
        return row[0] if row else None


def update_profile(
    connection: Any,
    user_id: int,
    full_name: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE app_users
               SET full_name = %(full_name)s
             WHERE user_id = %(user_id)s
            """,
            {"full_name": full_name, "user_id": user_id},
        )


def reset_password(
    connection: Any,
    user_id: int,
    password_hash: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE app_users
               SET password_hash = %(password_hash)s
             WHERE user_id = %(user_id)s
            """,
            {"password_hash": password_hash, "user_id": user_id},
        )
        cursor.execute(
            """
            DELETE FROM user_sessions
             WHERE user_id = %(user_id)s
            """,
            {"user_id": user_id},
        )


def reset_password_with_token(
    connection: Any,
    token: str,
    password_hash: str,
) -> bool:
    user_id = consume_reset_token(connection, token)
    if user_id is None:
        return False

    reset_password(connection, user_id, password_hash)
    return True


def update_password_keep_session(
    connection: Any,
    user_id: int,
    password_hash: str,
    session_token: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE app_users
               SET password_hash = %(password_hash)s
             WHERE user_id = %(user_id)s
            """,
            {"password_hash": password_hash, "user_id": user_id},
        )
        cursor.execute(
            """
            DELETE FROM user_sessions
             WHERE user_id = %(user_id)s
               AND token_hash <> %(token_hash)s
            """,
            {
                "user_id": user_id,
                "token_hash": hash_token(session_token),
            },
        )


def account_for_reset(
    connection: Any,
    email: str,
) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, full_name, email
              FROM app_users
             WHERE email = %(email)s
            """,
            {"email": email},
        )
        return _account(cursor)


def consume_reset_token(
    connection: Any,
    token: str,
) -> int | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id
              FROM account_tokens
             WHERE token_hash = %(token_hash)s
               AND purpose = 'reset_password'
               AND expires_at > UTC_TIMESTAMP()
             FOR UPDATE
            """,
            {"token_hash": hash_token(token)},
        )
        row = cursor.fetchone()
        if row is None:
            return None

        user_id = int(row[0])

        cursor.execute(
            """
            DELETE FROM account_tokens
             WHERE user_id = %(user_id)s
            """,
            {"user_id": user_id},
        )
        return user_id
