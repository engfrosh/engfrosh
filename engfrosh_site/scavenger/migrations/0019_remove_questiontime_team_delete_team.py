# Generated by Django 4.0.4 on 2022-07-11 23:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scavenger', '0018_alter_team_current_question'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questiontime',
            name='team',
        ),
        migrations.DeleteModel(
            name='Team',
        ),
    ]
