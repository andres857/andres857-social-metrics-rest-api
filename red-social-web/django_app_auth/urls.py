"""
URL configuration for django_app_auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from auth_app.views import google_login, google_callback, linkedin_login, linkedin_callback, GoogleLogin

from django.conf.urls import handler404, handler500

handler404 = 'auth_app.views.custom_404'
handler500 = 'auth_app.views.custom_500'

# Vista de prueba errores 500
# def homepage_view(request):
#    raise Exception("This is a test error")

urlpatterns = [
    #path("", homepage_view),  # new
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('auth_app.urls')),
    path('auth/google/login/', google_login, name='google_login'),
    path('auth/google/callback/', google_callback, name='google_callback'),
    path('auth/google/', GoogleLogin.as_view(), name='google_login_api'),
    path('auth/linkedin/login/', linkedin_login, name='linkedin_login'),
    path('auth/linkedin/callback/', linkedin_callback, name='linkedin_callback'),
    path('api/social-metrics/', include('social_metrics.urls')),
]
