# Generated by Django 5.1 on 2024-08-21 15:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social_metrics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='institution',
            name='type_institution',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.typeinstitution'),
        ),
    ]
