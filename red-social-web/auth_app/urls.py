from django.urls import path
from .views import LoginView, CustomRegisterView, GetCSRFToken, ForgotPasswordView, CustomLogoutView, ResetPasswordView, auth_status, user_detail, update_profile, change_password

urlpatterns = [
    # path('user-profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('get-csrf-token/', GetCSRFToken.as_view(), name='get_csrf_token'),
    path('logout/', CustomLogoutView.as_view(), name='custom_logout'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', CustomRegisterView.as_view(), name='register'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    path('user/detail/', user_detail, name='user_detail'),
    path('user/profile/', update_profile, name='update_profile'),
    path('user/change-password/', change_password, name='change_password'),
    
    #Validacion de autentificacion y suscripcion
    path('auth-status/', auth_status, name='auth-status'),
]