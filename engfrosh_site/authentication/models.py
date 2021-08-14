import datetime
import secrets

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def days5():
    return timezone.now() + datetime.timedelta(days=5)


def random_token():
    return secrets.token_urlsafe(42)


class DiscordUser(models.Model):
    """Linking Discord user to website user."""

    id = models.BigIntegerField("Discord ID", primary_key=True)
    discord_username = models.CharField(max_length=100, blank=True)
    discriminator = models.IntegerField(blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_index=True)
    access_token = models.CharField(max_length=40, blank=True)
    expiry = models.DateTimeField(blank=True, null=True)
    refresh_token = models.CharField(max_length=40, blank=True)

    class Meta:
        """Meta information for Discord Users."""

        verbose_name = "Discord User"
        verbose_name_plural = "Discord Users"

    def __str__(self) -> str:
        return f"{self.discord_username}#{self.discriminator}"

    def set_tokens(self, access_token, expires_in, refresh_token):
        """Set the user's discord tokens."""

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in - 10)
        self.save()


class MagicLink(models.Model):
    token = models.CharField(max_length=64, default=random_token)
    user = models.OneToOneField(User, models.CASCADE)
    expiry = models.DateTimeField(default=days5)
    delete_immediately = models.BooleanField(default=True)

    def link_used(self) -> bool:
        """Returns True if link can still be used, or False if not."""
        if self.delete_immediately:
            self.delete()
            return False

        if self.expiry < timezone.now() + datetime.timedelta(days=1):
            # Only 1 day left, do nothing
            return True

        else:
            self.expiry = timezone.now() + datetime.timedelta(days=1)
            self.save()
            return True
