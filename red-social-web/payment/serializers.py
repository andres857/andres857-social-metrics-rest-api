from rest_framework import serializers
from .models import SubscriptionPlan, PaymentTokenDiscount

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'title', 'imageCover', 'description', 'price', 'duration_days']
        
class PaymentTokenDiscountSerializer(serializers.ModelSerializer):
    subscription_plans = serializers.StringRelatedField(many=True)

    class Meta:
        model = PaymentTokenDiscount
        fields = ['id', 'token', 'discount', 'start_date', 'end_date', 'subscription_plans', 'created_at', 'updated_at']