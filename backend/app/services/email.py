import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import quote

from fastapi import HTTPException

from app.config import Settings


logger = logging.getLogger(__name__)


def send_account_email(
    settings: Settings,
    *,
    recipient: str,
    subject: str,
    action: str,
    token: str,
) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        raise HTTPException(
            status_code=503,
            detail="Email delivery is not configured. Set the SMTP settings in backend/.env.",
        )
    if bool(settings.smtp_username) != bool(settings.smtp_password):
        raise HTTPException(
            status_code=503,
            detail="Both SMTP username and password must be configured.",
        )
    if settings.smtp_starttls and settings.smtp_use_ssl:
        raise HTTPException(
            status_code=503,
            detail="Configure either SMTP STARTTLS or SMTP SSL, not both.",
        )
    if settings.smtp_username and not (
        settings.smtp_starttls or settings.smtp_use_ssl
    ):
        raise HTTPException(
            status_code=503,
            detail="Authenticated SMTP must use STARTTLS or SSL.",
        )

    url = f"{settings.frontend_url.rstrip('/')}/{action}?token={quote(token)}"
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = recipient
    message.set_content(
        f"Hello,\n\nUse the following link to continue with your Inventory Desk account:\n"
        f"{url}\n\nThis link expires in 30 minutes. If you did not request this, "
        "you can ignore this email.\n"
    )

    try:
        smtp_client = (
            smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=10,
                context=ssl.create_default_context(),
            )
            if settings.smtp_use_ssl
            else smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
        )
        with smtp_client as server:
            if settings.smtp_starttls:
                server.starttls()
                server.ehlo()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password or "")
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        logger.error("Could not deliver account email via configured SMTP.")
        raise HTTPException(
            status_code=503,
            detail="The account email could not be sent. Check the backend SMTP settings.",
        ) from error
