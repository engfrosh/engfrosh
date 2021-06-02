import requests
import datetime
from oauthlib.oauth2 import WebApplicationClient

import logging

logger = logging.getLogger("DiscordAPI")

DISCORD_API_URL = "https://discord.com/api"
TOKEN_URL_PATH = "/oauth2/token"
AUTHERIZATION_API_URL_PATH = "/oauth2/authorize"

# Temp db credentials
DATABASE = "engfrosh"
USER = "discord_engfrosh"
PASSWORD = "there-exercise-fenegel"
HOST = "localhost"
PORT = "5432"


class DiscordAPI():

    def __init__(self, client_id, client_secret, *, access_token=None, version=None, expires_in=None,
                 refresh_token=None, oauth_code=None, callback_url=None, expiry=None):

        if not (access_token or refresh_token or oauth_code and callback_url):
            raise Exception("Insufficient information passed to initialize API")

        if not (access_token and refresh_token) and oauth_code and callback_url:
            # If no tokens, get the tokens
            logger.info("No tokens provided, getting tokens with oauth code and callback url")
            credentials = get_tokens(oauth_code, callback_url, client_id, client_secret)

            access_token = credentials["access_token"]
            expires_in = credentials["expires_in"]
            refresh_token = credentials["refresh_token"]
            expiry = None

        self.access_token = access_token
        self.version = version
        self.refresh_token = refresh_token

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

        if self.access_token:
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            self.headers = None

    def get_user_info(self):
        url = self.discord_api_url + "/users/@me"

        response = requests.get(url, headers=self.headers)

        response.raise_for_status()

        return response.json()

    def get_user_id(self):
        return self.get_user_info()["id"]

    def get_tokens(self):
        if not self.expiry:
            raise Exception("No expiry info, cannot return tokens")
        expires_in = int((self.expiry - datetime.datetime.now()).total_seconds())
        return (self.access_token, expires_in, self.refresh_token)


def get_tokens(oauth_code, callback_url, client_id, client_secret):
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


def get_api_url(version=None):
    if not version:
        return DISCORD_API_URL
    else:
        return DISCORD_API_URL + f"/v{version}"


def get_authorization_url(version=None):
    return get_api_url(version) + AUTHERIZATION_API_URL_PATH


def get_token_url(version=None):
    return get_api_url(version) + TOKEN_URL_PATH
# endregion
