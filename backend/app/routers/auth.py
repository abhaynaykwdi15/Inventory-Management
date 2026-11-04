
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from mysql.connector import IntegrityError

from app.database import get_connection
from app.repositories import accounts
from app.schemas.auth import (
    AccountRead,
    LoginRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    RegisterRequest,
)
from app.services.auth_security import hash_password, new_token, verify_password
from app.services.database_errors import run_read, run_write


router = APIRouter(prefix="/auth", tags=["authentication"])

SESSION_COOKIE = "inventory_session"
_DUMMY_PASSWORD_HASH = hash_password("inventory-dummy-password")


def _settings(request: Request):
    return request.app.state.settings


def _set_session_cookie(
    response: Response,
    request: Request,
    token: str,
) -> None:
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
        raise HTTPException(
            status_code=401,
            detail="Sign in to continue.",
        )

    user = run_read(
        connection,
        lambda: accounts.get_session_account(connection, token),
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Your session expired. Please sign in again.",
        )

    with connection.cursor() as cursor:
        cursor.execute(
            "SET @inventory_actor = %s",
            (user["email"],),
        )

    request.state.session_token = token

    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    connection: Annotated[Any, Depends(get_connection)],
) -> dict[str, str]:

    email_unavailable = run_read(
        connection,
        lambda: accounts.email_is_unavailable(
            connection,
            payload.email,
        ),
    )

    if email_unavailable:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

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
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    return {
        "message": "Registration successful. You can now log in.",
        "user_id": str(user_id),
    }


@router.post("/login", response_model=AccountRead)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    connection: Annotated[Any, Depends(get_connection)],
) -> AccountRead:

    user = run_read(
        connection,
        lambda: accounts.get_account_by_email(
            connection,
            payload.email,
        ),
    )

    stored_hash = (
        user["password_hash"]
        if user
        else _DUMMY_PASSWORD_HASH
    )

    valid_password = verify_password(
        payload.password,
        stored_hash,
    )

    if user is None or not valid_password:
        raise HTTPException(
            status_code=401,
            detail="Email or password is incorrect.",
        )

    token = new_token()
    settings = _settings(request)

    expires_at = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(hours=settings.auth_session_hours)
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

    account = run_read(
        connection,
        lambda: accounts.get_account_by_id(
            connection,
            int(user["user_id"]),
        ),
    )

    return AccountRead.model_validate(account)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    response: Response,
    connection: Annotated[Any, Depends(get_connection)],
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Response:

    if token and len(token) <= 128:
        run_write(
            connection,
            lambda: accounts.delete_session(connection, token),
        )

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


@router.put("/profile", response_model=AccountRead)
def update_profile(
    payload: ProfileUpdateRequest,
    connection: Annotated[Any, Depends(get_connection)],
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> AccountRead:

    user_id = int(user["user_id"])

    if payload.email != user["email"]:
        email_unavailable = run_read(
            connection,
            lambda: accounts.email_is_unavailable(
                connection,
                payload.email,
                exclude_user_id=user_id,
            ),
        )

        if email_unavailable:
            raise HTTPException(
                status_code=409,
                detail="That email address is already in use.",
            )

    def save_profile() -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE app_users
                   SET full_name = %(full_name)s,
                       email = %(email)s,
                       pending_email = NULL,
                       email_verified = TRUE
                 WHERE user_id = %(user_id)s
                """,
                {
                    "full_name": payload.full_name,
                    "email": payload.email,
                    "user_id": user_id,
                },
            )

    run_write(connection, save_profile)

    updated = run_read(
        connection,
        lambda: accounts.get_account_by_id(connection, user_id),
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    return AccountRead.model_validate(updated)


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    connection: Annotated[Any, Depends(get_connection)],
    user: Annotated[dict[str, Any], Depends(require_user)],
    request: Request,
) -> dict[str, str]:

    user_id = int(user["user_id"])

    stored_hash = run_read(
        connection,
        lambda: accounts.password_hash_for_user(
            connection,
            user_id,
        ),
    )

    if stored_hash is None or not verify_password(
        payload.current_password,
        stored_hash,
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect.",
        )

    run_write(
        connection,
        lambda: accounts.update_password_keep_session(
            connection,
            user_id,
            hash_password(payload.new_password),
            request.state.session_token,
        ),
    )

    return {
        "message": "Your password has been changed."
    }
