from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('orders', views.create_order_t, name='orders'),
]