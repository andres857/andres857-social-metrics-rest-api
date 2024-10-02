from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from allauth.account.models import EmailAddress

from users.models import UserRole, Role

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'password2', 'first_name', 'last_name',
                  'phone', 'organization')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            # 'identification': {'required': True},
            'email': {'required': True},
            'organization': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Crear la entrada en account_emailaddress
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=False,
            primary=True
        )
        
        # Asignar el rol "general_user"
        general_user_role = Role.objects.get(identifier='=805MHj0')
        UserRole.objects.create(user=user, role=general_user_role)
        
        return user