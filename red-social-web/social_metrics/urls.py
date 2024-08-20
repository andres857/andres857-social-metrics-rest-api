from django.urls import path
from . import views

app_name = 'social_metrics'  # Esto define el espacio de nombres

urlpatterns = [
    path('institutions', views.get_all_institutions, name='institutions'),
    path('upload', views.procesar_datos_excel, name='upload'),
]