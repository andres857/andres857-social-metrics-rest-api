# Generated by Django 5.1 on 2024-09-15 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social_metrics', '0007_remove_institutionstatsbytype_institution_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetwork',
            name='percent_correction',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
