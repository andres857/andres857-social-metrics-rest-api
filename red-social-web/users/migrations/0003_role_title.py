# Generated by Django 5.1 on 2024-10-01 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_userrole_expires_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='title',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
