from django.urls import path
from . import views

app_name = 'social_metrics'  # Esto define el espacio de nombres

urlpatterns = [
    path('', views.manage_social_metrics, name='metrics'),
    path('dates', views.dates_collections, name='dates'),
    path('institutions', views.manage_institutions, name='institutions'),
    path("institutions/types/", views.list_institutions_for_category_and_date, name="list_institutions_for_category_and_date"),
    # path("institutions/types/<str:institution_type>", views.list_institutions_for_type_and_date, name="list_institutions_for_type_and_date")
    # path('institutions/categories', views.manage_institutions, name='categories'),
    # path('institutions/categories1', views.manage_institutions_oks, name='categories1'),
    path('social-network', views.manage_social_networks, name='social-network'),
    path("social-network/<int:id>", views.manage_social_networks, name="social-network-update"),
    path('upload', views.procesar_datos_excel, name='upload'),
    path('stats', views.manage_stats, name='stats'),
    path('youtube/statistics/', views.get_channel_stats_youtube_api_function, name='data_youtube'),
    path('youtube/bulk-statistics/', views.bulk_channel_stats, name='youtube_bulk_stats'),
]