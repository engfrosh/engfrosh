# Generated by Django 3.2.5 on 2021-09-03 01:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frosh', '0011_universityprogram'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdetails',
            name='invite_email_sent',
            field=models.BooleanField(default=False, verbose_name='Invite Email Sent'),
            preserve_default=False,
        ),
    ]
