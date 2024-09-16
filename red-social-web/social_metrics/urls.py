from django.urls import path
from . import views

app_name = 'social_metrics'  # Esto define el espacio de nombres

urlpatterns = [
    path('', views.manage_social_metrics, name='metrics'),
    path('institutions', views.manage_institutions, name='institutions'),
    path('institutions/categories', views.manage_institutions, name='categories'),
    path('social-network', views.manage_social_networks, name='social-network'),
    path("social-network/<int:id>", views.manage_social_networks, name="social-network-update"),
    path('upload', views.procesar_datos_excel, name='upload'),
    path('stats', views.manage_stats, name='stats'),
    path('youtube/statistics/', views.get_channel_stats_youtube_api_function, name='data_youtube'),
    path('youtube/bulk-statistics/', views.bulk_channel_stats, name='youtube_bulk_stats'),
]