# Generated by Django 5.1 on 2024-08-20 21:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('followers', models.IntegerField()),
                ('publications', models.IntegerField()),
                ('likes', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='CollectionDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('name_period', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('city', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=100)),
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
            name='CalculateMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('engagement_rate', models.FloatField()),
                ('metrics_base', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.basemetrics')),
            ],
        ),
        migrations.AddField(
            model_name='basemetrics',
            name='collectiondate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.collectiondate'),
        ),
        migrations.AddField(
            model_name='basemetrics',
            name='institution',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.institution'),
        ),
        migrations.AddField(
            model_name='basemetrics',
            name='socialnetwork',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_metrics.socialnetwork'),
        ),
    ]
