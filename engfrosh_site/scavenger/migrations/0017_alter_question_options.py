# Generated by Django 3.2.5 on 2021-08-14 21:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scavenger', '0016_team_finished'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='question',
            options={'permissions': [('guess_scav_question', 'Can guess for scav questions'), ('manage_scav', 'Can manage scav')], 'verbose_name': 'Scavenger Question', 'verbose_name_plural': 'Scavenger Questions'},
        ),
    ]