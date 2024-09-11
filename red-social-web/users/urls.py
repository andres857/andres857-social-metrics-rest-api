from django.urls import path
from .views import ListUsers, CreateUser, DeleteUser, UpdateUser

urlpatterns = [
    path('get-users/', ListUsers.as_view(), name='get-users'),
    path('create-user/', CreateUser.as_view(), name='create-user'),
    path('delete-user/<int:user_id>/', DeleteUser.as_view(), name='delete-user'),
    path('update-user/<int:user_id>/', UpdateUser.as_view(), name='update-user'),
]