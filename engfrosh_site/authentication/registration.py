"""Registration functions for helping register and initialize users."""

from .models import MagicLink
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils.encoding import iri_to_uri
from django.utils import timezone


def get_magic_link(user: User, hostname: str, login_path: str,
                   expires_in: timedelta = None,
                   delete_on_use: bool = True, redirect: str = None):
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
