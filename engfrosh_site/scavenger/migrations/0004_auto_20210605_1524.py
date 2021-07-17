# Generated by Django 3.2.3 on 2021-06-05 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scavenger', '0003_auto_20210605_1522'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionorder',
            name='order_number',
        ),
        migrations.AddField(
            model_name='questionorder',
            name='weight',
            field=models.IntegerField(default=0, primary_key=True, serialize=False, verbose_name='Order Number'),
            preserve_default=False,
        ),
    ]