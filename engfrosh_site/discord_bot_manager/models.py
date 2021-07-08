from django.db import models

from django.contrib.auth.models import Group

import uuid

from django.db.models.deletion import CASCADE

from django.utils import timezone


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


class Role(models.Model):
    role_id = models.PositiveBigIntegerField("Discord Role ID", primary_key=True)
    group_id = models.OneToOneField(Group, CASCADE)
