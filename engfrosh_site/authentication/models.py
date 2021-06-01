from django.db import models
from django.contrib.auth.models import User
import datetime


class DiscordUser(models.Model):
    id = models.BigIntegerField(primary_key=True)
    discord_username = models.CharField(max_length=100, blank=True)
    discriminator = models.IntegerField(blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_index=True)
    access_token = models.CharField(max_length=40, blank=True)
    expiry = models.DateTimeField(blank=True)
    refresh_token = models.CharField(max_length=40, blank=True)

    def set_tokens(self, access_token, expires_in, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in - 10)
        self.save()


