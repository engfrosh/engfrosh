# Generated by Django 3.2.5 on 2021-08-14 15:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scavenger', '0013_alter_question_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='question',
            options={'permissions': [('guess_scav_question', 'Can guess for scav questions')], 'verbose_name': 'Scavenger Question', 'verbose_name_plural': 'Scavenger Questions'},
        ),
    ]
