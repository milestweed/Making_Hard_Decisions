# Generated by Django 3.1.7 on 2021-04-29 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sc_app', '0013_auto_20210429_1846'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cbgstore',
            name='id',
        ),
        migrations.AddField(
            model_name='cbgstore',
            name='ID',
            field=models.IntegerField(default=0, primary_key=True, serialize=False),
        ),
    ]
