# Generated by Django 5.1 on 2024-08-20 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social_metrics', '0002_rename_name_period_collectiondate_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basemetrics',
            name='collectiondate',
        ),
        migrations.RenameField(
            model_name='basemetrics',
            old_name='likes',
            new_name='reactions',
        ),
        migrations.AddField(
            model_name='basemetrics',
            name='date_collection',
            field=models.DateField(null=True),
        ),
        migrations.DeleteModel(
            name='CollectionDate',
        ),
    ]
