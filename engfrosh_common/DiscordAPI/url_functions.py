"""Functions for getting urls for the api."""

from typing import Optional


DISCORD_API_URL = "https://discord.com/api"
TOKEN_URL_PATH = "/oauth2/token"
AUTHORIZATION_API_URL_PATH = "/oauth2/authorize"


def get_api_url(version: Optional[int] = None):
    """
    Return the discord api endpoint url.

    Does not include the trailing slash.

    """
    if not version:
        return DISCORD_API_URL
    else:
        return DISCORD_API_URL + f"/v{version}"


def get_authorization_url(version=None):
    """Return the authorization api endpoint url."""
    return get_api_url(version) + AUTHORIZATION_API_URL_PATH


def get_token_url(version=None):
    """Return the token api endpoint url."""
    return get_api_url(version) + TOKEN_URL_PATH
