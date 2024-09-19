# Generated by Django 5.1 on 2024-09-19 19:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscription',
            old_name='mercadopago_id',
            new_name='collection_id',
        ),
        migrations.AddField(
            model_name='subscription',
            name='collection_status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscription',
            name='external_reference',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='merchant_account_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='merchant_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='payment_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='payment_type',
            field=models.CharField(blank=True, choices=[('account_money', 'Account Money'), ('credit_card', 'Credit Card'), ('debit_card', 'Debit Card'), ('bank_transfer', 'Bank Transfer'), ('other', 'Other')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='preference_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='processing_mode',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='site_id',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='subscription',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
