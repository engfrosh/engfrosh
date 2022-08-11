# Generated by Django 3.2.3 on 2021-06-02 00:00

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('discord_bot_manager', '0002_auto_20210531_2212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discordcommandstatus',
            name='command_id',
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, unique=True, verbose_name='Command ID'),
        ),
    ]