from django.db import models
from django.contrib.auth.models import Group
from django.db.models.deletion import CASCADE


class Team(models.Model):
    display_name = models.CharField("Team Name", max_length=64)
    group = models.OneToOneField(Group, on_delete=CASCADE, primary_key=True)
    coin_amount = models.BigIntegerField("Coin Amount", default=0)

    def __str__(self):
        return str(self.display_name)
