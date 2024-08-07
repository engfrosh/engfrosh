"""Custom authentication backend to support magic links and discord credentials."""

import random
import string
import logging
import os
from typing import Union

import credentials
from common_models.models import DiscordUser, MagicLink, Team, PuzzleStream, TeamPuzzleActivity

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth import logout

from pyaccord.DiscordUserAPI import DiscordUserAPI

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)
PARENT_PARENT_DIRECTORY = os.path.dirname(PARENT_DIRECTORY)


logger = logging.getLogger(__name__)


def register(access_token=None, expires_in=None, refresh_token=None, user=None, username=None, email=None,
             password=None, discord_oauth_code=None, callback_url=None) -> Union[User, None]:
    """Register a new Discord user.

    The user can be tied to an existing User account if `user` is passed.
    If not, a new account is created with the passed information.
    """

    # Get User Info
    try:
        discord_api = DiscordUserAPI(client_id=credentials.DISCORD_CLIENT_ID,
                                     client_secret=credentials.DISCORD_CLIENT_SECRET,
                                     access_token=access_token,
                                     expires_in=expires_in, refresh_token=refresh_token,
                                     oauth_code=discord_oauth_code,
                                     callback_url=callback_url)
        discord_user_info = discord_api.get_user_info()

        discord_user_id = discord_user_info["id"]
        discord_username = discord_user_info["username"].encode("utf-8").decode('utf-8', 'ignore').encode("utf-8")
        discord_discriminator = discord_user_info["discriminator"]

        # Check if user is already registered
        try:
            discord_user = DiscordUser.objects.get(id=discord_user_id)
            if discord_user:
                raise DiscordUserAlreadyExistsError
        except DiscordUser.DoesNotExist:
            pass

        # If no given User account to associate with, create a new one
        if not user:
            if not username:
                s = f"{discord_username}+{discord_discriminator}-"
                username = s + "".join(random.choice(string.ascii_letters + string.digits) for i in range(8))
            user = User.objects.create_user(username, email, password)  # type: ignore
            user.save()
            group = Group(name=username)
            group.save()
            group.user_set.add(user)
            perm = Permission.objects.filter(codename="guess_scavenger_puzzle").first()
            group.permissions.add(perm)
            group.save()
            team = Team(group=group, display_name=username)
            team.save()
            streams = PuzzleStream.objects.filter(enabled=True, default=True)
            for s in streams:
                puz = s.first_enabled_puzzle
                try:
                    pa = TeamPuzzleActivity(team=team, puzzle=puz)
                    pa.save()
                except Exception:
                    pass

        # Create new DiscordUser
        discord_user = DiscordUser(
            id=discord_user_id, user=user, discord_username=discord_username, discriminator=discord_discriminator)
        discord_user.set_tokens(*discord_api.get_tokens())
        discord_user.save()

        return user
    except:  # noqa: E722
        logger.error("Failed to register user. Info: AT:", access_token, "OT:", discord_oauth_code, "CB:", callback_url)
        return None


class DiscordAuthBackend(BaseBackend):
    """Custom authentication backend, supports magic links and discord credentials."""

    def authenticate(
            self, request, discord_user_id=None, discord_access_token=None,
            discord_expires_in=None, discord_refresh_token=None, discord_oauth_code=None,
            callback_url=None, magic_link_token=None) -> Union[User, None]:
        """Authenticates users with discord or magic link."""

        logger.info("Trying to authenticate with DiscordAuthBackend.authenticate")

        if request.user.is_authenticated:
            logger.info("User is already logged in!")
            logout(request)
            logger.info("Logged out user!")

        if magic_link_token:
            logger.info("Trying to authenticate with magic link token")
            try:
                if magic_link := MagicLink.objects.get(token=magic_link_token):
                    # if magic_link.expiry > timezone.now():
                    user = magic_link.user
                    return user
                    # else:
                    #     # Link is expired
                    #     magic_link.delete()
                    #     return None

            except Exception:
                pass

            return None

        # If discord id is passed
        if discord_user_id:
            logger.info(f"Trying to authenticate with discord_user_id: {discord_user_id}")
            try:
                return DiscordUser.objects.get(id=discord_user_id).user
            except DiscordUser.DoesNotExist:
                logger.info(f"Discord user id: {discord_user_id} does not exist on the system.")
                return None

        try:
            client = DiscordUserAPI(
                client_id=credentials.DISCORD_CLIENT_ID, client_secret=credentials.DISCORD_CLIENT_SECRET, version=8,
                access_token=discord_access_token, expires_in=discord_expires_in, refresh_token=discord_refresh_token,
                oauth_code=discord_oauth_code, callback_url=callback_url)
        except Exception:
            return None

        try:
            discord_user = DiscordUser.objects.get(id=client.get_user_id())
            logger.info("Found discord user in system")
        except DiscordUser.DoesNotExist:
            logger.info("User does not exist in system")
            return None

        discord_user.set_tokens(*client.get_tokens())
        return discord_user.user

    def get_user(self, user_id=None, discord_id=None):
        """Returns the User object given by user or discord id."""

        if user_id:
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return None

        if discord_id:
            try:
                return DiscordUser.objects.get(id=discord_id).user
            except (DiscordUser.DoesNotExist, User.DoesNotExist):
                return None

        return None


class DiscordUserAlreadyExistsError(BaseException):
    """Exception raised when a discord user already exists."""
