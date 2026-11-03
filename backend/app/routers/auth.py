import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from mysql.connector import IntegrityError

from app.config import Settings
from app.database import get_connection
from app.repositories import accounts
from app.schemas.auth import (
    AccountRead,
    EmailRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenRequest,
)
from app.services.auth_security import hash_password, new_token, verify_password
from app.services.database_errors import run_read, run_write
from app.services.email import send_account_email, validate_email_configuration


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
SESSION_COOKIE = "inventory_session"
_DUMMY_PASSWORD_HASH = hash_password("inventory-dummy-password")
GENERIC_EMAIL_RESPONSE = {
    "message": "If that address is eligible, an email with next steps will arrive shortly."
}


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _set_session_cookie(response: Response, request: Request, token: str) -> None:
    settings = _settings(request)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.auth_session_hours * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


def require_user(
    request: Request,
    connection: Annotated[Any, Depends(get_connection)],
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> dict[str, Any]:
    if not token or len(token) > 128:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    user = run_read(connection, lambda: accounts.get_session_account(connection, token))
    if user is None:
        raise HTTPException(status_code=401, detail="Your session expired. Please sign in again.")
    with connection.cursor() as cursor:
        cursor.execute("SET @inventory_actor = %s", (user["email"],))
    request.state.session_token = token
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    connection: Annotated[Any, Depends(get_connection)],
) -> dict[str, str]:
    validate_email_configuration(_settings(request))
    email_unavailable = run_read(
        connection,
        lambda: accounts.email_is_unavailable(
            connection,
            payload.email,
        ),
    )
    if email_unavailable:
        return GENERIC_EMAIL_RESPONSE

    try:
        user_id = accounts.create_account(
            connection,
            full_name=payload.full_name,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        connection.commit()
    except IntegrityError:
        connection.rollback()
        return GENERIC_EMAIL_RESPONSE

    token = new_token()
    run_write(
        connection,
        lambda: accounts.create_email_token(
            connection,
            user_id=user_id,
            token=token,
            purpose="verify_email",
        ),
    )
    send_account_email(
        _settings(request),
        recipient=payload.email,
        subject="Verify your Inventory Desk email",
        action="verify-email",
        token=token,
    )
    return {"message": "Account created. Check your email to verify your address before signing in."}


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    connection: Annotated[Any, Depends(get_connection)],
) -> AccountRead:
    user = run_read(
        connection,
        lambda: accounts.get_account_by_email(connection, payload.email),
    )
    stored_hash = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
    valid_password = verify_password(payload.password, stored_hash)
    if user is None or not valid_password:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    if not user["email_verified"]:
        raise HTTPException(
            status_code=403,
            detail="Verify your email address before signing in.",
        )

    token = new_token()
    settings = _settings(request)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        hours=settings.auth_session_hours
    )
    run_write(
        connection,
        lambda: accounts.create_session(
            connection,
            user_id=int(user["user_id"]),
            token=token,
            expires_at=expires_at,
        ),
    )
    _set_session_cookie(response, request, token)
    return AccountRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    connection: Annotated[Any, Depends(get_connection)],
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Response:
    if token and len(token) <= 128:
        run_write(connection, lambda: accounts.delete_session(connection, token))
    settings = _settings(request)
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=AccountRead)
def current_account(
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> AccountRead:
    return AccountRead.model_validate(user)


@router.post("/verify-email")
def verify_email(
    payload: TokenRequest,
    connection: Annotated[Any, Depends(get_connection)],
) -> dict[str, str]:
    verified = run_write(
        connection,
        lambda: accounts.verify_email_token(connection, payload.token),
    )
    if not verified:
        raise HTTPException(status_code=400, detail="This verification link is invalid or expired.")
    return {"message": "Email verified. You can now sign in."}


@router.post("/resend-verification")
def resend_verification(
    payload: EmailRequest,
    request: Request,
    connection: Annotated[Any, Depends(get_connection)],
) -> dict[str, str]:
    user = run_read(
        connection,
        lambda: accounts.get_account_by_email(connection, payload.email),
    )
    if user and not user["email_verified"]:
        token = new_token()
        run_write(
            connection,
            lambda: accounts.create_email_token(
                connection,
                user_id=int(user["user_id"]),
                token=token,
                purpose="verify_email",
            ),
        )
        send_account_email(
            _settings(request),
            recipient=payload.email,
            subject="Verify your Inventory Desk email",
            action="verify-email",
            token=token,
        )
    return GENERIC_EMAIL_RESPONSE


@router.post("/forgot-password")
def forgot_password(
    payload: EmailRequest,
    request: Request,
    connection: Annotated[Any, Depends(get_connection)],
) -> dict[str, str]:
    user = run_read(
        connection,
        lambda: accounts.account_for_reset(connection, payload.email),
    )
    if user:
        token = new_token()
        run_write(
            connection,
            lambda: accounts.create_email_token(
                connection,
                user_id=int(user["user_id"]),
                token=token,
                purpose="reset_password",
            ),
        )
        try:
            send_account_email(
                _settings(request),
                recipient=payload.email,
                subject="Reset your Inventory Desk password",
                action="reset-password",
                token=token,
            )
        except HTTPException as error:
            logger.error("Password-reset email could not be delivered: %s", error.detail)
    return GENERIC_EMAIL_RESPONSE


@router.post("/reset-password")
def reset_password(
    payload: PasswordResetRequest,
    connection: Annotated[Any, Depends(get_connection)],
) -> dict[str, str]:
    reset = run_write(
        connection,
        lambda: accounts.reset_password_with_token(
            connection,
            payload.token,
            hash_password(payload.password),
        ),
    )
    if not reset:
        raise HTTPException(status_code=400, detail="This password-reset link is invalid or expired.")
    return {"message": "Password updated. Sign in with your new password."}


@router.put("/profile", response_model=AccountRead)
def update_profile(
    payload: ProfileUpdateRequest,
    request: Request,
    connection: Annotated[Any, Depends(get_connection)],
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> AccountRead:
    if payload.email != user["email"]:
        email_unavailable = run_read(
            connection,
            lambda: accounts.email_is_unavailable(
                connection,
                payload.email,
                exclude_user_id=int(user["user_id"]),
            ),
        )
        if email_unavailable:
            raise HTTPException(status_code=409, detail="That email address is already in use.")
        token = new_token()
        run_write(
            connection,
            lambda: accounts.set_pending_email(
                connection,
                int(user["user_id"]),
                payload.email,
            ),
        )
        run_write(
            connection,
            lambda: accounts.create_email_token(
                connection,
                user_id=int(user["user_id"]),
                token=token,
                purpose="change_email",
            ),
        )

    run_write(
        connection,
        lambda: accounts.update_profile(
            connection,
            int(user["user_id"]),
            payload.full_name,
        ),
    )

    if payload.email != user["email"]:
        send_account_email(
            _settings(request),
            recipient=payload.email,
            subject="Confirm your new Inventory Desk email",
            action="verify-email",
            token=token,
        )

    updated = run_read(
        connection,
        lambda: accounts.get_account_by_id(connection, int(user["user_id"])),
    )
    assert updated is not None
    return AccountRead.model_validate(updated)


@router.delete("/profile/pending-email", status_code=status.HTTP_204_NO_CONTENT)
def cancel_email_change(
    connection: Annotated[Any, Depends(get_connection)],
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> Response:
    run_write(
        connection,
        lambda: accounts.cancel_pending_email(connection, int(user["user_id"])),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    connection: Annotated[Any, Depends(get_connection)],
    user: Annotated[dict[str, Any], Depends(require_user)],
    request: Request,
) -> dict[str, str]:
    stored_hash = run_read(
        connection,
        lambda: accounts.password_hash_for_user(connection, int(user["user_id"])),
    )
    if stored_hash is None or not verify_password(payload.current_password, stored_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    run_write(
        connection,
        lambda: accounts.update_password_keep_session(
            connection,
            int(user["user_id"]),
            hash_password(payload.new_password),
            request.state.session_token,
        ),
    )
    return {"message": "Your password has been changed."}
