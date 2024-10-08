# Generated by Django 5.1 on 2024-09-16 04:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social_metrics', '0008_socialnetwork_percent_correction'),
    ]

    operations = [
        migrations.RenameField(
            model_name='socialnetwork',
            old_name='percent_correction',
            new_name='percentage_correction_social_networks',
        ),
        migrations.AddField(
            model_name='socialnetwork',
            name='percentage_correction_type_institutions',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
