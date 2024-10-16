from django.urls import path
from . import views

app_name = 'social_metrics'  # Esto define el espacio de nombres

urlpatterns = [
    path('', views.manage_social_metrics, name='metrics'),
    path('upload', views.procesar_datos_excel, name='upload'),
    path('dates', views.dates_collections, name='dates'),

    path('institutions/', views.manage_institutions, name='institutions'),
    path("institutions-types", views.list_institutions_for_category_and_date, name="list-institutions"),

    path('social-network', views.manage_social_networks, name='social-network'),
    path("social-network/<int:id>", views.manage_social_networks, name="social-network-update"),
    
    path('stats', views.manage_stats, name='stats'),

    path('followers', views.followers_uniques, name='followers'),
    path('followers/compensacion', views.followers_uniques_compensacion, name='followers-compensacion'),

    path('followers/social-networks', views.followers_uniques_by_social_networks, name='followers-social-networks'),
    path('followers/social-networks/compensacion', views.followers_uniques_by_social_networks_compensacion, name='followers-social-networks-compensacion'),

    path('youtube/statistics/', views.get_channel_stats_youtube_api_function, name='data_youtube'),
    path('youtube/bulk-statistics/', views.bulk_channel_stats, name='youtube_bulk_stats'),
]