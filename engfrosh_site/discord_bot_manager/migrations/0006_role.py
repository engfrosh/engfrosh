# Generated by Django 3.2.3 on 2021-06-19 00:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('discord_bot_manager', '0005_alter_discordcommandstatus_command_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('role_id', models.IntegerField(primary_key=True, serialize=False, verbose_name='Discord Role ID')),
                ('group_id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='auth.group')),
            ],
        ),
    ]
