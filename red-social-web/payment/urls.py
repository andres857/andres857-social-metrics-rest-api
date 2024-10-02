from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    #path('orders', views.create_order_t, name='orders'),
    path('create-subscription/', views.create_preference, name='create_subscription'),
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
    path('api/mercadopago/webhook/', views.mercadopago_webhook, name='mercadopago_webhook'),
    path('get/pricing/', views.pricing, name='get_pricing'),
]