"""Servicio de envio de emails (F14).

Best-effort SMTP via smtplib + ssl. Si SMTP_USER/SMTP_PASSWORD no
estan configurados o si el envio falla por cualquier motivo
(timeout, credenciales invalidas, red), se loggea el error y la
funcion retorna sin propagar la excepcion: el endpoint
/forgot-password debe devolver 200 igualmente para mantener la
politica anti-enumeration. Si el email no llega, el usuario lo
sabra al no recibir nada en su bandeja, pero nunca filtramos
"este email no existe" via 5xx.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("clipcatcher.email")


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    """Envia el email de reset al destinatario. Nunca lanza excepciones."""
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_password:
        logger.error(
            "SMTP no configurado (SMTP_USER/SMTP_PASSWORD vacios). "
            "Email a %s NO enviado.",
            to_email,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = "ClipCatcher · Recupera tu contraseña"
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.set_content(
        "Hola,\n\n"
        "Hemos recibido una solicitud para restablecer la contraseña de tu "
        "cuenta de ClipCatcher.\n\n"
        f"Para crear una nueva contraseña, abre este enlace:\n{reset_url}\n\n"
        "El enlace caduca en 1 hora y solo se puede usar una vez.\n\n"
        "Si no has sido tu, ignora este mensaje y tu cuenta seguira con la "
        "contraseña actual.\n\n"
        "— ClipCatcher\n"
    )

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            context=context,
            timeout=15,
        ) as smtp:
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        logger.info("password_reset email enviado a %s", to_email)
    except Exception as exc:  # noqa: BLE001 — best-effort, no propagar
        logger.error(
            "Fallo enviando password_reset email a %s: %s",
            to_email,
            exc,
        )


__all__ = ["send_password_reset_email"]
