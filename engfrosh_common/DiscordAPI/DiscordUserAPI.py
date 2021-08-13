"""API abstraction for performing actions on Discord Users."""

import requests
import datetime
import logging

from typing import List, Optional, Union
from oauthlib.oauth2 import WebApplicationClient

from .url_functions import get_api_url, get_authorization_url, get_token_url


logger = logging.getLogger("DiscordAPI")


class DiscordUserAPI():
    """Class for performing actions on a discord user."""

    def __init__(self, *, client_id=None, client_secret=None, access_token=None, version=None, expires_in=None,
                 refresh_token=None, oauth_code=None, callback_url=None, expiry=None, bot_token: str = None):
        """Initialize Discord User API."""

        if not (access_token and refresh_token or oauth_code and callback_url):
            raise ValueError("Insufficient information passed to initialize API")

        if not (access_token and refresh_token) and oauth_code and callback_url:
            # If no tokens, get the tokens
            logger.info("No tokens provided, getting tokens with oauth code and callback url")
            try:
                credentials = get_tokens(oauth_code, callback_url, client_id, client_secret)
            except requests.exceptions.HTTPError as e:
                logger.error(
                    f"Failed to get tokens from discord."
                    f"\nResponse: {e.response.status_code} {e.response.reason} {e.response.content}"
                    f"\nRequest: {e.request.method} {e.request.headers} {e.request.body}",
                    exc_info=e)
                raise e

            access_token = credentials["access_token"]
            expires_in = credentials["expires_in"]
            refresh_token = credentials["refresh_token"]
            expiry = None

        self.access_token = access_token
        self.version = version
        self.refresh_token = refresh_token
        self.bot_token = bot_token

        self.user_id: Union[int, None] = None

        if expiry:
            self.expiry = expiry
            logger.debug(f"Expiry was passed, setting to {expiry}")
        elif expires_in:
            self.expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in - 10)
            logger.debug(f"expires_in set, setting expiry as {self.expiry}")
        else:
            self.expiry = None
            logger.info("No expiry info given, setting expiry to None")

        self.discord_api_url = get_api_url(self.version)

    def get_user_info(self):
        url = self.discord_api_url + "/users/@me"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        response = requests.get(url, headers=headers)

        response.raise_for_status()

        return response.json()

    def get_user_id(self) -> Union[int, None]:
        """Get the user id for the current credentials if not already cached."""
        if self.user_id:
            return self.user_id

        try:
            user_id = self.get_user_info()["id"]
        except KeyError as e:
            logger.error("Failed to get user id because of key error.", exc_info=e)
            return None

        if not user_id:
            logger.error("Failed to get user id.", stack_info=True)
            return None

        self.user_id = user_id
        return user_id

    def get_tokens(self):
        if not self.expiry:
            raise Exception("No expiry info, cannot return tokens")
        expires_in = int((self.expiry - datetime.datetime.now()).total_seconds())
        return (self.access_token, expires_in, self.refresh_token)

    def add_user_to_guild(
            self, guild_id: int, *, user_id: Optional[int] = None, nickname: Optional[str] = None,
            roles: Optional[List[int]] = None, mute: Optional[bool] = None, deaf: Optional[bool] = None) -> bool:
        """
        Add the user to the specified guild.

        Args:
            user_id: discord user id, if provided will skip requesting the id associated with the credentials.
        """

        if not user_id:
            user_id = self.get_user_id()

        if not user_id:
            logger.error("No valid discord user id to use.")
            return False

        logger.debug(f"Trying to add discord user id {user_id} to guild {guild_id}")

        url = self.discord_api_url + f"/guilds/{guild_id}/members/{user_id}"
        logger.debug(f"Request url: {url}")

        headers = {
            "User-Agent": "WebsiteServerClient (engfrosh.com, 1)",
            "authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }

        data = {"access_token": self.access_token}

        if nickname:
            data["nick"] = nickname
        if roles:
            data["roles"] = roles
        if mute:
            data["mute"] = mute
        if deaf:
            data["deaf"] = deaf

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 201:
            logger.info(f"Successfully added user with id {user_id} to guild with id {guild_id}")
            return True

        elif response.status_code == 204:
            logger.warning(f"User with id {user_id} already is a member of the guild with id {guild_id}")
            return False

        else:
            logger.error(
                f"Could not add user with id {user_id} to guild with id {guild_id}")
            return False


def get_tokens(oauth_code, callback_url, client_id, client_secret):
    """Get the tokens OAuth tokens for the user via the discord api."""

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': oauth_code,
        'redirect_uri': callback_url
    }

    headers = {
        "Content-Type": 'application/x-www-form-urlencoded'
    }

    response = requests.post(get_token_url(), headers=headers, data=data)
    response.raise_for_status()
    return response.json()

# region URL Functions


def build_oauth_authorize_url(client_id, callback_url, scope, prompt="consent", version=None):
    oauth_client = WebApplicationClient(client_id)

    authorization_request = oauth_client.prepare_authorization_request(
        authorization_url=get_authorization_url(version),
        redirect_url=callback_url,
        scope=scope,
        prompt=prompt)

    return authorization_request[0]


# endregion
