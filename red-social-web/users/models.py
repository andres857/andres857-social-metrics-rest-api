from django.db import models
from auth_app.models import CustomUser as User

from django.utils import timezone

class Role(models.Model):

    identifier = models.CharField(max_length=225, unique=True, primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_active_users(self):
        return self.users.filter(is_active=True)
    
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    subscription_type = models.CharField(max_length=50, blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    def has_expired(self):
        return self.expires_at is not None and self.expires_at < timezone.now()

    def is_active(self):
        return not self.has_expired()

    @classmethod
    def active(cls):
        return cls.objects.filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now()))