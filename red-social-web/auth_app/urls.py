from django.urls import path
from . import views

urlpatterns = [
    path('user-profile/', views.UserProfileView.as_view(), name='user_profile'),
    # Añade aquí más rutas de API según sea necesario
]