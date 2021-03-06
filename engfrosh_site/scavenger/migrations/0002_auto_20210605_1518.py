# Generated by Django 3.2.3 on 2021-06-05 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scavenger', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='identifier',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='question',
            name='id',
            field=models.IntegerField(editable=False, primary_key=True, serialize=False, verbose_name='Question ID'),
        ),
    ]
