# Generated by Django 5.1 on 2024-09-20 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0004_customuser_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='photoprofile_path',
            field=models.ImageField(blank=True, max_length=300, null=True, upload_to='profile_pics/'),
        ),
    ]
