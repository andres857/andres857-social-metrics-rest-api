# Generated by Django 5.1 on 2024-10-15 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0010_alter_subscription_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTokensAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('token', models.CharField(max_length=100, unique=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('subscription_plans', models.ManyToManyField(related_name='tokens', to='payment.subscriptionplan')),
            ],
            options={
                'verbose_name': 'Payment Token Access',
                'verbose_name_plural': 'Payment Tokens Access',
            },
        ),
    ]
