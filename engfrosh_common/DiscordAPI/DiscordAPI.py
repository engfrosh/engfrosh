"""API calls for performing Discord API actions."""

from typing import Dict, List, Optional, Union
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

    def get_channel(self, channel_id: int) -> dict:
        """Get the channel information."""

        url = get_api_url(self.api_version) + f"/channels/{channel_id}"
        response = requests.get(url, headers=self.headers)

        response.raise_for_status()

        json_response = response.json()

        logger.debug(f"Got channel info: {json_response}")

        return json_response

    def get_channel_overwrites(self, channel_id: int) -> List[Dict[str, Union[str, int]]]:
        """Get all the current overwrites for a channel."""

        channel = self.get_channel(channel_id)

        return channel["permission_overwrites"]

    def modify_channel_overwrites(self, channel_id: int, overwrites: Union[dict, List[dict]]):
        """Change the permission overwrites for the given channel.

        Parameters
        ==========
            overwrites: a dictionary or a list of dictionaries representing all the overwrites.

        """

        data = {}

        if isinstance(overwrites, dict):
            overwrites["allow"] = str(overwrites["allow"])
            overwrites["deny"] = str(overwrites["deny"])
            data["permission_overwrites"] = [overwrites]
        elif isinstance(overwrites, list):
            for i in range(len(overwrites)):
                overwrites[i]["allow"] = str(overwrites[i]["allow"])
                overwrites[i]["deny"] = str(overwrites[i]["deny"])
            data["permission_overwrites"] = overwrites

        url = get_api_url(self.api_version) + f"/channels/{channel_id}"
        response = requests.patch(url, headers=self.headers, json=data)

        response.raise_for_status()

        json_response = response.json()

        logger.debug(f"Successfully modified channel overwrites. Channel now: {json_response}")

        return json_response
