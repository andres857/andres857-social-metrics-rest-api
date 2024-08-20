from django.urls import path
from .views import LoginView, GetCSRFToken

urlpatterns = [
    # path('user-profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('get-csrf-token/', GetCSRFToken.as_view(), name='get_csrf_token'),
    path('login/', LoginView.as_view(), name='login'),
    # Añade aquí más rutas de API según sea necesario
]