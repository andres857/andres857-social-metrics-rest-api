# Generated by Django 5.1 on 2024-09-20 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0003_remove_customuser_type_identification'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='organization',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
