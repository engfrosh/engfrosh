# Generated by Django 3.2.3 on 2021-07-01 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scavenger', '0009_settings_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='answer',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
    ]
