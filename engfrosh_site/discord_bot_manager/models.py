from django.db import models

from django.contrib.auth.models import Group

import uuid

from django.db.models.deletion import CASCADE


class DiscordCommandStatus(models.Model):
    command_id = models.UUIDField("Command ID", primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    status = models.CharField("Command Status", max_length=4,
                              choices=[("PEND", "Pending"),
                                       ("SUCC", "Succeeded"),
                                       ("FAIL", "Failed")])
    timeout = models.DateTimeField("Command Callback Timeout")
    error_message = models.CharField("Error Message", max_length=100, blank=True)

    def succeeded(self):
        if self.status == "SUCC":
            return True
        else:
            return False

    def get_status(self):
        return (self.status, self.error_message)

    def __string__(self):
        return str(self.command_id)


class ScavChannel(models.Model):
    channel_id = models.BigIntegerField(primary_key=True)
    group = models.OneToOneField(Group, on_delete=CASCADE, db_index=True)

    # TODO add __string__ method
    