# Generated by Django 3.2.5 on 2021-08-30 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discord_bot_manager', '0008_alter_role_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelTag',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64, unique=True, verbose_name='Tag Name')),
            ],
            options={
                'verbose_name': 'Channel Tag',
                'verbose_name_plural': 'Channel Tags',
            },
        ),
        migrations.CreateModel(
            name='DiscordChannel',
            fields=[
                ('id', models.PositiveBigIntegerField(primary_key=True, serialize=False, verbose_name='Discord Channel ID')),
                ('name', models.CharField(blank=True, default='', max_length=100, verbose_name='Discord Channel Name')),
                ('type', models.IntegerField(choices=[(0, 'GUILD_TEXT'), (1, 'DM'), (2, 'GUILD_VOICE')], verbose_name='Channel Type')),
                ('tags', models.ManyToManyField(to='discord_bot_manager.ChannelTag')),
            ],
            options={
                'verbose_name': 'Discord Channel',
                'verbose_name_plural': 'Discord Channels',
                'permissions': [('lock_channels', 'Can lock or unlock discord channels.')],
            },
        ),
    ]
