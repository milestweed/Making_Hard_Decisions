# Generated by Django 3.1.7 on 2021-03-21 12:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sc_app', '0002_movement_yr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='info',
            name='brand',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sc_app.colors'),
        ),
    ]