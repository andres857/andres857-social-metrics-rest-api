from django.urls import path
from .views import LoginView, GetCSRFToken, ForgotPasswordView, CustomLogoutView

urlpatterns = [
    # path('user-profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('get-csrf-token/', GetCSRFToken.as_view(), name='get_csrf_token'),
    path('logout/', CustomLogoutView.as_view(), name='custom_logout'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='api_forgot_password'),
    # Añade aquí más rutas de API según sea necesario
]