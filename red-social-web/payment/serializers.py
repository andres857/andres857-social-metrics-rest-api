from rest_framework import serializers
from datetime import datetime
from .models import Subscription, SubscriptionPlan, PaymentTokenDiscount, PaymentTokensAccess

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'title', 'imageCover', 'description', 'price', 'duration_days']
        
class PaymentTokenDiscountSerializer(serializers.ModelSerializer):
    subscription_plans = serializers.StringRelatedField(many=True)

    class Meta:
        model = PaymentTokenDiscount
        fields = ['id', 'title', 'token', 'discount', 'start_date', 'end_date', 'subscription_plans', 'created_at', 'updated_at']
        
class PaymentTokenAccessSerializer(serializers.ModelSerializer):
    subscription_plans = serializers.StringRelatedField(many=True)

    class Meta:
        model = PaymentTokensAccess
        fields = ['id', 'title', 'token', 'start_date', 'end_date', 'subscription_plans', 'is_active']