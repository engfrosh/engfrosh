"""API calls for performing Discord API actions."""

from typing import Optional
import requests
import logging
from .url_functions import get_api_url

logger = logging.getLogger("DiscordAPI")


class DiscordAPI:
    """Class for performing generic Discord API actions."""

    def __init__(self, bot_token: str, *, api_version: Optional[int] = None) -> None:
        """Initialize Discord API."""

        self.bot_token = bot_token
        self.api_version = api_version

        self.headers = {
            "User-Agent": "WebsiteServerClient (engfrosh.com, 1)",
            "authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }

    def create_guild_role(self, guild_id: int, *,
                          name: Optional[str] = None,
                          permissions: Optional[int] = None,
                          color: Optional[int] = None,
                          hoist: Optional[bool] = False,
                          mentionable: Optional[bool] = False) -> int:
        """
        Create a new guild role.

        Parameters
        ----------
            mentionable: whether the role can be mentioned
            hoist: whether the role should be shown separately
            permissions, the bitwise representation of permissions
            color, hex color code

        Returns: guild id
        """

        data = {}

        for title, item in [
            ("name", name),
            ("permissions", permissions),
            ("color", color),
            ("hoist", hoist),
            ("mentionable", mentionable)
        ]:
            if item is not None:
                data[title] = item

        url = get_api_url(self.api_version) + f"/guilds/{guild_id}/roles"
        response = requests.post(url, headers=self.headers, json=data)

        response.raise_for_status()

        json_response = response.json()

        role_id = json_response["id"]
        role_name = json_response["name"]

        logger.info(f"Created new guild role {role_name} with snowflake: {role_id}")

        return role_id
