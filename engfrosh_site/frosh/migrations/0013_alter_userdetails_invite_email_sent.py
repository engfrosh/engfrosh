# Generated by Django 3.2.5 on 2021-09-03 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frosh', '0012_userdetails_invite_email_sent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetails',
            name='invite_email_sent',
            field=models.BooleanField(default=False, verbose_name='Invite Email Sent'),
        ),
    ]
