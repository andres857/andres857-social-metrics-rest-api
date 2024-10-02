from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()

    def __str__(self):
        return self.name

class Subscription(models.Model):
    PAYMENT_TYPES = (
        ('account_money', 'Account Money'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Campos adicionales de Mercado Pago
    collection_id = models.CharField(max_length=255, blank=True, null=True)
    collection_status = models.CharField(max_length=50, blank=True, null=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    external_reference = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPES, blank=True, null=True)
    merchant_order_id = models.CharField(max_length=255, blank=True, null=True)
    preference_id = models.CharField(max_length=255, blank=True, null=True)
    site_id = models.CharField(max_length=10, blank=True, null=True)
    processing_mode = models.CharField(max_length=50, blank=True, null=True)
    merchant_account_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        plan_name = self.plan.name if self.plan else 'No plan'
        return f"{self.user.username}'s {plan_name} subscription"
    
class PaymentTokenDiscount(models.Model):
    token = models.CharField(max_length=100, unique=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    discount = models.IntegerField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
