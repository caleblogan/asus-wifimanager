# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-08 22:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wifimanager', '0003_auto_20170808_1507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connectionsample',
            name='connection_time',
            field=models.CharField(max_length=15),
        ),
    ]
