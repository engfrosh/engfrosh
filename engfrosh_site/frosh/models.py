"""Database models for Frosh App."""

from django.db import models
from django.contrib.auth.models import Group, User
from django.db.models.deletion import CASCADE


class Team(models.Model):
    """Frosh Team model, for the actual teams in Frosh."""

    display_name = models.CharField("Team Name", max_length=64, unique=True)
    group = models.OneToOneField(Group, on_delete=CASCADE, primary_key=True, related_name="frosh_team")
    coin_amount = models.BigIntegerField("Coin Amount", default=0)
    color = models.PositiveIntegerField("Hex Color Code", null=True, blank=True, default=None)

    class Meta:
        """Team Meta information."""

        permissions = [
            ("change_team_coin", "Can change the coin amount of a team."),
            ("view_team_coin_standings", "Can view the coin standings of all teams.")
        ]
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return str(self.display_name)


class FroshRole(models.Model):
    """Frosh role, such as Frosh, Facil, Head, Planning."""

    name = models.CharField("Role Name", max_length=64, unique=True)
    group = models.OneToOneField(Group, on_delete=CASCADE, primary_key=True)

    class Meta:
        """Frosh Role Meta information."""

        verbose_name = "Frosh Role"
        verbose_name_plural = "Frosh Roles"

    def __str__(self) -> str:
        return self.name


class UserDetails(models.Model):
    """Details pertaining to users without fields in the default User."""

    user = models.OneToOneField(User, on_delete=CASCADE, primary_key=True)
    name = models.CharField("Name", max_length=64)
    pronouns = models.CharField("Pronouns", max_length=20, blank=True)

    class Meta:
        """User Details Meta information."""

        verbose_name = "User Details"
        verbose_name_plural = "Users' Details"

    def __str__(self) -> str:
        return f"{self.name} ({self.user.username})"
