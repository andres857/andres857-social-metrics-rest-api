# Generated by Django 5.1 on 2024-08-21 13:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('city', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='SocialNetwork',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='TypeInstitution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('url', models.URLField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BaseMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('followers', models.IntegerField()),
                ('publications', models.IntegerField()),
                ('reactions', models.IntegerField()),
                ('date_collection', models.DateField(blank=True, null=True)),
                ('engagment_rate', models.FloatField(blank=True, null=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.institution')),
                ('socialnetwork', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.socialnetwork')),
            ],
        ),
        migrations.AddField(
            model_name='institution',
            name='type_institution',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.typeinstitution'),
        ),
    ]
