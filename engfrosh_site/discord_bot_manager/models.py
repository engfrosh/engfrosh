"""Database Models for the Discord Bot Manager App."""

import logging
import credentials
import uuid

from typing import Dict, List

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.deletion import CASCADE
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils import timezone


from engfrosh_common.DiscordAPI.DiscordAPI import DiscordAPI

logger = logging.getLogger("DiscordBotManager.Models")


class Role(models.Model):
    """Relates a Django group to a discord role."""

    role_id = models.PositiveBigIntegerField("Discord Role ID", primary_key=True)
    group_id = models.OneToOneField(Group, CASCADE)

    class Meta:
        """Meta information for Discord roles."""

        verbose_name = "Discord Role"
        verbose_name_plural = "Discord Roles"

    def __str__(self) -> str:
        return self.group_id.name


class DiscordOverwrite(models.Model):
    """Represents Discord Permission Overwrites."""

    descriptive_name = models.CharField(max_length=100, blank=True, default="")
    id = models.AutoField("Overwrite ID", primary_key=True)
    user_id = models.PositiveBigIntegerField("User or Role ID")
    type = models.IntegerField(choices=[(0, "Role"), (1, "Member")])
    allow = models.PositiveBigIntegerField("Allowed Overwrites")
    deny = models.PositiveBigIntegerField("Denied Overwrites")

    class Meta:
        """Discord Overwrite Meta Info."""

        verbose_name = "Discord Permission Overwrite"
        verbose_name_plural = "Discord Permission Overwrites"

    def __str__(self) -> str:
        if self.descriptive_name:
            return self.descriptive_name
        elif self.type == 0:
            try:
                role = Role.objects.get(role_id=self.user_id)
                return f"Role Overwrite for {role.group_id.name}"
            except ObjectDoesNotExist:
                return f"Role Overwrite: {self.user_id}"
        else:
            return f"User Overwrite: {self.user_id}"

    @property
    def verbose(self) -> str:
        """Return a verbose representation of the object."""
        return f"<DiscordOverwrite: id = {self.id}, user_id = {self.user_id}, allow = {self.allow}, deny = {self.deny}"

    @property
    def to_encoded_dict(self) -> dict:
        """Return the encoded dictionary version."""
        d = {
            "id": self.user_id,
            "allow": str(self.allow),
            "deny": str(self.deny)
        }
        return d


def overwrite_from_dict(d: dict) -> DiscordOverwrite:
    """Create a DiscordOverwrite object from the json encoded response dictionary."""
    return DiscordOverwrite(
        user_id=int(d["id"]),
        type=d["type"],
        allow=int(d["allow"]),
        deny=int(d["deny"])
    )


class DiscordCommandStatus(models.Model):
    command_id = models.UUIDField("Command ID", primary_key=True, unique=True, default=uuid.uuid4)
    status = models.CharField("Command Status", max_length=4,
                              choices=[("PEND", "Pending"),
                                       ("SUCC", "Succeeded"),
                                       ("FAIL", "Failed")])
    timeout = models.DateTimeField("Command Callback Timeout")
    error_message = models.CharField("Error Message", max_length=100, blank=True)
    command_time = models.DateTimeField("Command Time", default=timezone.now)

    def succeeded(self):
        if self.status == "SUCC":
            return True
        else:
            return False

    def get_status(self):
        return (self.status, self.error_message)

    def __string__(self):
        return f"[{str(self.command_id)}]@[{str(self.command_time)}]"


class ScavChannel(models.Model):
    channel_id = models.BigIntegerField(primary_key=True)
    group = models.OneToOneField(Group, on_delete=CASCADE, db_index=True)

    # TODO add __string__ method
    # Todo make the one to one field reference a scav team instead of group


class ChannelTag(models.Model):
    """Tags classifying Discord Channels."""

    id = models.AutoField(primary_key=True)
    name = models.CharField("Tag Name", max_length=64, unique=True)

    class Meta:
        """ChannelTag Meta information."""

        verbose_name = "Channel Tag"
        verbose_name_plural = "Channel Tags"

    def __str__(self) -> str:
        return self.name

    def lock(self):
        """Lock the channel."""

        for channel in DiscordChannel.objects.filter(tags__id=self.id):
            channel.lock()

    def unlock(self):
        """Unlock the channel."""
        for channel in DiscordChannel.objects.filter(tags__id=self.id):
            channel.unlock()


class DiscordChannel(models.Model):
    """Discord Channel Object."""

    id = models.PositiveBigIntegerField("Discord Channel ID", primary_key=True)
    name = models.CharField("Discord Channel Name", max_length=100, unique=False, blank=True, default="")
    tags = models.ManyToManyField(ChannelTag, blank=True)
    type = models.IntegerField("Channel Type", choices=[(0, "GUILD_TEXT"), (1, "DM"), (2, "GUILD_VOICE")])
    locked_overwrites = models.ManyToManyField(DiscordOverwrite, blank=True)
    unlocked_overwrites = models.ManyToManyField(
        DiscordOverwrite, related_name="unlocked_channel_overwrites", blank=True)

    class Meta:
        """Discord Channel Model Meta information."""

        permissions = [
            ("lock_channels", "Can lock or unlock discord channels.")
        ]

        verbose_name = "Discord Channel"
        verbose_name_plural = "Discord Channels"

    def __str__(self) -> str:
        if self.name:
            return self.name
        else:
            return f"<Discord Channel {self.id}>"

    @property
    def overwrites(self) -> List[DiscordOverwrite]:
        """Gets all the current overwrites for the channel."""
        api = DiscordAPI(credentials.BOT_TOKEN, api_version=settings.DEFAULT_DISCORD_API_VERSION)
        raw_overwrites = api.get_channel_overwrites(self.id)

        overwrites = []
        for ro in raw_overwrites:
            o = overwrite_from_dict(ro)
            overwrites.append(o)

        return overwrites

    @property
    def overwrite_dict(self) -> Dict[int, DiscordOverwrite]:
        """Get all the current overwrites for the channel as a dictionary with the user id as the key."""

        o_dict = {}

        overwrites = self.overwrites
        for ov in overwrites:
            o_dict[ov.user_id] = ov

        return o_dict

    def lock(self) -> bool:
        """Lock the channel, only affecting the overwrites in the channel info."""

        logger.debug(f"Locking channel {self.name}({self.id})")

        overwrites = self.overwrite_dict
        for o in self.locked_overwrites.all():
            overwrites[o.user_id] = o

        logger.debug(f"Permission Overwrites: {[o.verbose for o in overwrites.values()]}")

        encoded_overwrites = []
        for k, v in overwrites.items():
            encoded_overwrites.append(v.to_encoded_dict)

        api = DiscordAPI(credentials.BOT_TOKEN, api_version=settings.DEFAULT_DISCORD_API_VERSION)
        api.modify_channel_overwrites(self.id, encoded_overwrites)

        return True

    def unlock(self) -> bool:
        """Unlock the channel, only affecting the overwrites in the channel info."""

        overwrites = self.overwrite_dict
        for o in self.unlocked_overwrites.all():
            overwrites[o.user_id] = o

        encoded_overwrites = []
        for k, v in overwrites.items():
            encoded_overwrites.append(v.to_encoded_dict)

        api = DiscordAPI(credentials.BOT_TOKEN, api_version=settings.DEFAULT_DISCORD_API_VERSION)
        api.modify_channel_overwrites(self.id, encoded_overwrites)

        return True
