from django.urls import path
from .views import LoginView, GetCSRFToken, ForgotPasswordView, CustomLogoutView, auth_status, user_detail, update_profile, change_password

urlpatterns = [
    # path('user-profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('get-csrf-token/', GetCSRFToken.as_view(), name='get_csrf_token'),
    path('logout/', CustomLogoutView.as_view(), name='custom_logout'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='api_forgot_password'),
    
    path('user/detail/', user_detail, name='user_detail'),
    path('user/profile/', update_profile, name='update_profile'),
    path('user/change-password/', change_password, name='change_password'),
    
    #Validacion de autentificacion
    path('auth-status/', auth_status, name='auth-status'),
]