"""Registration functions for helping register and initialize users."""

import logging
import random
import string
from typing import Optional
from authentication.models import MagicLink
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils.encoding import iri_to_uri
from django.utils import timezone
from frosh.models import FroshRole, Team, UserDetails
from management.email import send_email

logger = logging.getLogger("Management.Registration")


class UserAlreadyExistsError(Exception):
    """Exception raised when a user already exists in the database."""


def get_magic_link(user: User, hostname: str, login_path: str,
                   expires_in: Optional[timedelta] = None,
                   delete_on_use: bool = True, redirect: str = None) -> str:
    """Returns the full url as specified. Invalidates any previous magic links.

    Args:
        hostname(str): needs to include the protocol, example `https://example.com` and no ending slash
        login_path(str): of the form `/accounts/login`
        redirect(str): a non encoded string representing the redirect url

    """

    if expires_in is None:
        expires_in = timedelta(days=3)

    try:
        existing = MagicLink.objects.get(user=user)
        existing.delete()
    except MagicLink.DoesNotExist:
        pass

    magic_link = MagicLink(user=user, expiry=timezone.now() + expires_in, delete_immediately=delete_on_use)

    if redirect is not None:
        redirect_str = f"&redirect={iri_to_uri(redirect)}"
    else:
        redirect_str = ""

    link = f"{hostname}{login_path}?auth={magic_link.token}{redirect_str}"

    magic_link.save()

    return link


DEFAULT_MAGIC_LINK_EMAIL_TEXT = """Here is your magic link to log into the EngFrosh site: {link}"""
DEFAULT_MAGIC_LINK_EMAIL_HTML = """<p><a href='{link}' >Here</a> is your magic link to log into the EngFrosh site."""
DEFAULT_MAGIC_LINK_EMAIL_SUBJECT = "Your EngFrosh Login"


def email_magic_link(user: User, hostname: str, login_path: str, sender_email: str, *,
                     expires_in: Optional[timedelta] = None, delete_on_use: bool = True,
                     redirect: Optional[str] = None, subject: Optional[str] = None,
                     body_text: Optional[str] = None, body_html: Optional[str] = None):
    """Creates a new magic link for the user and emails it to them.

    If body_text and body_html are passed they should have {link} provided to format with
    when the link is generated.

    """

    link = get_magic_link(user, hostname, login_path, expires_in, delete_on_use, redirect)

    if not body_text:
        body_text = DEFAULT_MAGIC_LINK_EMAIL_TEXT
    if not body_html:
        body_html = DEFAULT_MAGIC_LINK_EMAIL_HTML
    if not subject:
        subject = DEFAULT_MAGIC_LINK_EMAIL_SUBJECT

    return send_email(user=user, sender_email=sender_email, subject=subject,
                      body_text=body_text.format(link=link), body_html=body_html.format(link=link))


def create_user_initialize(name: str, email: str, role: FroshRole, team: Optional[Team] = None) -> User:
    """Creates a new user with the specified details, initializes their account with other passed details."""

    # Check that the email has not already been added
    if User.objects.filter(email=email).exists():
        logger.error(f"User with email {email} already exists in database.")
        raise UserAlreadyExistsError()

    username = name.replace(" ", "_") + "-" + "".join(random.choice(string.ascii_letters + string.digits)
                                                      for i in range(8))
    name_split = name.split()

    if len(name_split) == 2:
        first_name = name_split[0]
        last_name = name_split[1]
    else:
        first_name = ""
        last_name = name

    user = User.objects.create_user(username, email)  # type: ignore
    user.first_name = first_name
    user.last_name = last_name
    user.save()

    user_details = UserDetails(user=user, name=name)
    user_details.save()

    role.group.user_set.add(user)

    if team:
        team.group.user_set.add(user)

    return user
