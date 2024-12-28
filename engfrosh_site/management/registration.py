"""Registration functions for helping register and initialize users."""

import logging
import random
import string
from typing import Optional
import credentials
from django.core.exceptions import ObjectDoesNotExist
from common_models.models import MagicLink
from django.contrib.auth.models import User, Group
from datetime import timedelta
from django.utils.encoding import iri_to_uri
from django.utils import timezone
from common_models.models import FroshRole, Team, UserDetails, UniversityProgram, DiscordUser, DiscordRole, get_client
from management.email import send_email


logger = logging.getLogger("Management.Registration")


class UserAlreadyExistsError(Exception):
    """Exception raised when a user already exists in the database."""


def get_magic_link(user: User, hostname: str, login_path: str,
                   expires_in: Optional[timedelta] = None,
                   delete_on_use: bool = True, redirect: Optional[str] = None) -> str:
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


DEFAULT_MAGIC_LINK_EMAIL_TEXT = \
    """Welcome to EngFrosh!
Here is your magic link to log into the EngFrosh site and Discord server: {link}

If you need any help or any questions, please email websupport@engfrosh.com"""

DEFAULT_MAGIC_LINK_EMAIL_HTML = \
    """<html lang='en'>
        <body>
            <img src='data:image/jpg;base64,{logo}' alt='EngFrosh logo' style='text-align: center;' /><br/>
            <h1>Welcome to EngFrosh!</h1><br/>
            <p><a href='{link}' >Here</a> is your magic link to log into the EngFrosh site and Discord server.</p>
            <br/>
            <p>If you need any help or any questions,
            please email <a href="mailto:websupport@engfrosh.com">websupport@engfrosh.com</a>
            <br/>
            <br/>
            {link}
            </p>
        </body>
    </html>
    """
# Note, google tends to get rid of some link elements.
DEFAULT_MAGIC_LINK_EMAIL_SUBJECT = "Welcome to the EngFrosh Discord and Website!"


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

    res = send_email(user=user, sender_email=sender_email, subject=subject,
                     body_text=body_text.format(link=link), body_html=body_html.format(link=link, logo=""))

    if res:
        try:
            user_details = UserDetails.objects.get(user=user)
        except ObjectDoesNotExist:
            user_details = UserDetails(user=user, name=user.get_full_name())
        user_details.invite_email_sent = True
        user_details.save()

    return res


def compute_discord_name(user):
    details = md.UserDetails.objects.filter(user=user).first()
    if details.override_nick is not None:
        return details.override_nick
    pronouns = details.pronouns
    name = user.first_name
    if user.last_name:
        name += " " + user.last_name[:1]
    if len(pronouns) > 0:
        name += " ("
        for i in range(len(pronouns)-1):
            if len(name + pronouns[i].name + " ") > 31:
                break
            name += pronouns[i].name + " "
        name += pronouns[len(pronouns)-1].name + ")"
    return name


def create_user_initialize(name: str, email: str, role: FroshRole, team: Optional[Team] = None,
                           program: Optional[UniversityProgram] = None, size: Optional[str] = None,
                           rafting=False, hardhat=False, allergies="", sweater_size=None) -> User:
    """Creates a new user with the specified details, initializes their account with other passed details."""

    name_split = name.split()

    if len(name_split) == 2:
        first_name = name_split[0]
        last_name = name_split[1]
    else:
        first_name = ""
        last_name = name
    # Check that the email has not already been added
    if User.objects.filter(email=email).exists():
        logger.info(f"User with email {email} already exists in database. Updating!")
        user = User.objects.filter(email=email).first()
        if user.is_staff:
            raise UserAlreadyExistsError()
        details = UserDetails.objects.filter(user=user).first()
        if details is None:
            details = UserDetails(user=user, name=name, shirt_size=size,
                                  allergies=allergies, rafting=rafting, hardhat=hardhat,
                                  sweater_size=sweater_size)
        else:
            details.name = name
            details.shirt_size = size
            details.allergies = allergies
            details.rafting = rafting
            details.hardhat = hardhat
            details.sweater_size = sweater_size
            old_role = details.role
            if old_role is not None:
                Group.objects.filter(name=old_role).first().user_set.remove(user)
            old_team = details.team
            if old_team is not None:
                old_team.group.user_set.remove(user)
            programs = UniversityProgram.objects.all().values("group")
            for g in programs:
                if user in g.user_set:
                    g.user_set.remove(user)

        role.group.user_set.add(user)
        if team:
            team.group.user_set.add(user)
        if program:
            program.group.user_set.add(user)
        details.save()
        discord = DiscordUser.objects.filter(user=user).first()
        if discord is not None:
            # Change discord groups
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            client = get_client()
            groups = user.groups.all()
            discord_role_ids = []
            for g in groups:
                try:
                    query = DiscordRole.objects.filter(group_id=g)
                    for role in query:
                        if role.secondary_group is None or role.secondary_group in groups:
                            discord_role_ids.append(role.role_id)
                except ObjectDoesNotExist:
                    continue

            client.set_roles_for_member(credentials.GUILD_ID, discord.id, discord_role_ids)
            name = compute_discord_name(user)
            print("New nick: " + name)
            client.change_user_nickname(credentials.GUILD_ID, discord.id, name)
            return user

    username = name.replace(" ", "_") + "-" + "".join(random.choice(string.ascii_letters + string.digits)
                                                      for i in range(8))
    user = User.objects.create_user(username, email)  # type: ignore
    user.first_name = first_name
    user.last_name = last_name
    user.save()

    user_details = UserDetails(user=user, name=name, shirt_size=size,
                               allergies=allergies, rafting=rafting, hardhat=hardhat,
                               sweater_size=sweater_size)
    user_details.save()

    role.group.user_set.add(user)

    if team:
        team.group.user_set.add(user)

    if program:
        program.group.user_set.add(user)

    return user
