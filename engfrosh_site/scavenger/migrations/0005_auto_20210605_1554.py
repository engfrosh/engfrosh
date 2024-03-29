# Generated by Django 3.2.3 on 2021-06-05 19:54

from django.db import migrations, models
import common_models.models


class Migration(migrations.Migration):

    dependencies = [
        ('scavenger', '0004_auto_20210605_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='display_filename',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='hint',
            name='file',
            field=models.FileField(blank=True, upload_to=common_models.models.hint_path),
        ),
        migrations.AlterField(
            model_name='hint',
            name='image',
            field=models.ImageField(blank=True, upload_to=common_models.models.hint_path),
        ),
        migrations.AlterField(
            model_name='question',
            name='file',
            field=models.FileField(blank=True, upload_to=common_models.models.question_path),
        ),
        migrations.AlterField(
            model_name='question',
            name='image',
            field=models.ImageField(blank=True, upload_to=common_models.models.question_path),
        ),
    ]
