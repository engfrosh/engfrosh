# Generated by Django 3.2.3 on 2021-06-05 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frosh', '0002_rename_name_team_display_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='coin_amount',
            field=models.BigIntegerField(default=0, verbose_name='Coin Amount'),
        ),
    ]
