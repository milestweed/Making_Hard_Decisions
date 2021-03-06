# Generated by Django 3.1.7 on 2021-03-24 03:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sc_app', '0005_auto_20210321_1525'),
    ]

    operations = [
        migrations.CreateModel(
            name='CbgInfo',
            fields=[
                ('cbgID', models.FloatField(primary_key=True, serialize=False)),
                ('geometry', models.TextField()),
                ('population', models.FloatField()),
                ('med_age', models.FloatField()),
                ('med_hh_income', models.FloatField()),
                ('bachelor_degree', models.FloatField()),
                ('asian', models.FloatField()),
                ('hispanic', models.FloatField()),
                ('black', models.FloatField()),
                ('white', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='CbgStore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patronage', models.FloatField()),
                ('year', models.IntegerField()),
                ('cbg', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='sc_app.cbginfo')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='sc_app.info')),
            ],
        ),
    ]
