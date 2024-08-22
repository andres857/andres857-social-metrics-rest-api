from django.urls import path
from . import views

app_name = 'social_metrics'  # Esto define el espacio de nombres

urlpatterns = [
    path('', views.manage_social_metrics, name='metrics'),
    path('institutions', views.create_institution, name='institutions'),
    path('social-network', views.create_social_network, name='social-network'),
    path('upload', views.procesar_datos_excel, name='upload'),
]