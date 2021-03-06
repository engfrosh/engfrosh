# Generated by Django 3.2.5 on 2021-08-31 23:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discord_bot_manager', '0011_auto_20210831_1902'),
    ]

    operations = [
        migrations.AddField(
            model_name='discordoverwrite',
            name='descriptive_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='discordchannel',
            name='locked_overwrites',
            field=models.ManyToManyField(blank=True, to='discord_bot_manager.DiscordOverwrite'),
        ),
        migrations.AlterField(
            model_name='discordchannel',
            name='unlocked_overwrites',
            field=models.ManyToManyField(blank=True, related_name='unlocked_channel_overwrites', to='discord_bot_manager.DiscordOverwrite'),
        ),
    ]
