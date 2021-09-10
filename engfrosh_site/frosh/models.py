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

    def to_dict(self):
        """Get the dict representation of the team."""
        return {
            "team_id": self.group.id,
            "team_name": self.display_name,
            "coin_amount": self.coin_amount,
            "color_number": self.color,
            "color_code": self.color_code
        }

    @property
    def color_code(self):
        """The hex color code string of the team's color."""
        if self.color is not None:
            return "#{:06x}".format(self.color)
        else:
            return None


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


class UniversityProgram(models.Model):
    """Map a role as a course program."""

    name = models.CharField("Program Name", max_length=64, unique=True)
    group = models.OneToOneField(Group, on_delete=CASCADE, primary_key=True)

    class Meta:
        """University Program Meta Information."""

        verbose_name = "Program"
        verbose_name_plural = "Programs"

    def __str__(self) -> str:
        return self.name


class UserDetails(models.Model):
    """Details pertaining to users without fields in the default User."""

    user = models.OneToOneField(User, on_delete=CASCADE, primary_key=True)
    name = models.CharField("Name", max_length=64)
    pronouns = models.CharField("Pronouns", max_length=20, blank=True)
    invite_email_sent = models.BooleanField("Invite Email Sent", default=False)

    class Meta:
        """User Details Meta information."""

        verbose_name = "User Details"
        verbose_name_plural = "Users' Details"

    def __str__(self) -> str:
        return f"{self.name} ({self.user.username})"


class DiscordBingoCards(models.Model):
    """Lists bingo cards and their assigned discord ids."""

    discord_id = models.PositiveBigIntegerField(db_index=True, unique=True)
    bingo_card = models.PositiveIntegerField(primary_key=True)

    class Meta:
        """Discord Bingo Card Meta Information."""

        verbose_name = "Discord Bingo Card"
        verbose_name_plural = "Discord Bingo Cards"

    def __str__(self) -> str:
        return f"<Bingo Card {self.bingo_card} assigned to {self.discord_id}>"


class VirtualTeam(models.Model):
    """Tracks Virtual Teams and their discord ids."""

    role_id = models.PositiveBigIntegerField(primary_key=True)
    num_members = models.PositiveIntegerField(unique=False, default=0)

    class Meta:
        """Virtual Team Meta Information."""

        verbose_name = "Virtual Team"
        verbose_name_plural = "Virtual Teams"

    def __str__(self) -> str:
        return f"<Virtual Team {self.role_id} with {self.num_members} members>"
