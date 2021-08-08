"""Adds send email function for Django Users."""

from engfrosh_common.AWS_SES import send_SES
from django.contrib.auth.models import User

import logging

logger = logging.getLogger("Management.Email")


def send_email(*, user: User, sender_email: str, subject: str, body_text: str, body_html: str) -> bool:
    """Send an email to the email associated with a Django User."""
    if not user.email:
        logger.error(f"User {user} does not have an email to send to.")
        return False
    return send_SES(sender_email, user.email, subject, body_text, body_html)
