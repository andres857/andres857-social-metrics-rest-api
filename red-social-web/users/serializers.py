from rest_framework import serializers
from auth_app.models import CustomUser
from .models import Role, UserRole

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['identifier', 'name', 'description','title']

class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer()

    class Meta:
        model = UserRole
        fields = ['role']

class UserSerializer(serializers.ModelSerializer):
    user_roles = UserRoleSerializer(many=True, read_only=True)
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'identification', 'is_active', 'organization', 'user_roles']  # Añade o quita campos según necesites
        

class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    is_superuser = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = CustomUser
        fields = ['identification', 'email', 'password', 'first_name', 'last_name', 'phone', 'is_superuser']

    def create(self, validated_data):
        is_superuser = validated_data.pop('is_superuser', False)
        user = CustomUser.objects.create_user(**validated_data)
        if is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save()
        return user
    
    
class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['identification', 'email', 'first_name', 'last_name', 'phone', 'is_staff']  # Ajusta según tus campos
        extra_kwargs = {
            'identification': {'required': False},
            'email': {'required': False}
        }

    def update(self, instance, validated_data):
        is_staff = validated_data.pop('is_staff', False)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if is_staff:
            instance.is_superuser = False
            instance.is_staff = True
        instance.save()
        return instance