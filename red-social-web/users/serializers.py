from rest_framework import serializers
from auth_app.models import CustomUser
from .models import Role, UserRole

from payment.models import Subscription

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['identifier', 'name', 'description','title']

class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer()

    class Meta:
        model = UserRole
        fields = ['role']
        
class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'active', 'start_date', 'end_date']

class UserSerializer(serializers.ModelSerializer):
    user_roles = UserRoleSerializer(many=True, read_only=True)
    subscriptions = SubscriptionSerializer(many=True, read_only=True)  # Incluye las suscripciones

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'organization', 'user_roles', 'subscriptions']
        
class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_superuser = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'is_superuser']

    def create(self, validated_data):
        is_superuser = validated_data.pop('is_superuser', False)
        user = CustomUser.objects.create_user(**validated_data)
        if is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save()
        return user
    

class UpdateUserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=['user', 'admin', 'superadmin'], required=False)  # Ajusta según tus roles

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone', 'is_staff', 'role']  # Añade 'role' a los campos
        extra_kwargs = {
            'email': {'required': False}
        }

    def update(self, instance, validated_data):
        role = validated_data.pop('role', None)  # Obtén el rol si está presente
        is_staff = validated_data.pop('is_staff', False)

        # Lógica para activar is_staff o is_superuser según el rol
        if role in ['admin', 'superadmin']:
            instance.is_staff = True
            instance.is_superuser = (role == 'superadmin')  # Activa is_superuser solo si es superadmin
        else:
            instance.is_staff = False
            instance.is_superuser = False

        # Actualiza los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
