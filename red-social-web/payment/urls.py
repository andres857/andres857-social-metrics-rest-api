from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('create-subscription/', views.create_preference, name='create_subscription'),
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
    path('api/mercadopago/webhook/', views.mercadopago_webhook, name='mercadopago_webhook'),
    path('get/pricing/', views.pricing, name='get_pricing'),
    
    path('create-token/', views.create_token_endpoint, name='create-token'),
    path('list-tokens/', views.list_tokens_endpoint, name='list-tokens'),
    path('tokens/<str:token>/', views.get_token_details, name='get_token_details'),
    path('tokens/delete/<str:token>/', views.delete_token, name='delete_token'),
    
    # Nuevas rutas para los planes de suscripción
    path('subscription-plans/', views.subscription_plan_list_create, name='subscription-plan-list-create'),
    path('subscription-plans/<int:pk>/', views.subscription_plan_detail, name='subscription-plan-detail'),
]