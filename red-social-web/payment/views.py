import os
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseBadRequest

from django.conf import settings


from dateutil.relativedelta import relativedelta
import json
import logging
logger = logging.getLogger(__name__)

from .models import Subscription, SubscriptionPlan

# Mercado Pago SDK
import mercadopago
# Add Your credentials
User = get_user_model()
MEI_TOKEN = os.environ.get('MEI_TOKEN')
sdk = mercadopago.SDK(MEI_TOKEN)

@csrf_exempt
def create_preference(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido"}, status=405)

    if not MEI_TOKEN:
        logger.error("MEI_TOKEN no está configurado")
        return JsonResponse({"error": "Error de configuración del servidor"}, status=500)

    try:
        data = json.loads(request.body)
        plans = data.get('plans', [])
        user_id = data.get('user_id')

        logger.info(f"Creando preferencia para usuario {user_id} con planes {plans}")

        if not all([plans, user_id]):
            return JsonResponse({"error": "Se requieren planes y user_id"}, status=400)

        user = get_object_or_404(User, id=user_id)

        total_price = 0
        items = []
        subscriptions = []

        for plan_name in plans:
            plan = get_object_or_404(SubscriptionPlan, name=plan_name)
            total_price += float(plan.price)
            items.append({
                "title": plan.description,
                "quantity": 1,
                "currency_id": "COP",
                "unit_price": float(plan.price)
            })

        preference_data = {
            "items": items,
            "payer": {
                "name": user.first_name,
                "last_name": user.last_name,
                "email": user.email
            },
            "back_urls": {
                "success": f"{settings.BASE_URL}/payment/success/",
                "failure": f"{settings.BASE_URL}/payment/failure/",
                "pending": f"{settings.BASE_URL}/payment/pending/"
            },
            "auto_return": "approved",
            "statement_descriptor": "Redes Sociales Colombia",
            "external_reference": str(user.id),
        }

        logger.debug(f"Datos de preferencia: {preference_data}")

        preference_response = sdk.preference().create(preference_data)
        
        logger.debug(f"Respuesta de MercadoPago: {preference_response}")

        if 'response' not in preference_response:
            return JsonResponse({
                "error": "Error al crear la preferencia en MercadoPago",
                "mercadopago_response": preference_response
            }, status=500)

        preference = preference_response["response"]

        if "id" not in preference or "init_point" not in preference:
            return JsonResponse({
                "error": "Respuesta incompleta de MercadoPago",
                "mercadopago_response": preference
            }, status=500)

        # Crear una suscripción para cada plan
        start_date = timezone.now()
        for plan_name in plans:
            plan = SubscriptionPlan.objects.get(name=plan_name)
            end_date = start_date + relativedelta(days=plan.duration_days)

            subscription = Subscription.objects.create(
                user=user,
                active=False,
                start_date=start_date,
                end_date=end_date,
                preference_id=preference['id'],
                site_id=preference.get('site_id'),
                processing_mode='aggregator',
                plan_id = plan.id
                # total_price=float(plan.price),
            )
            #subscription.plan_id.add(plan.id)
            subscriptions.append(subscription)

        return JsonResponse({
            "id": preference["id"],
            "init_point": preference["init_point"],
            "sandbox_init_point": preference.get("sandbox_init_point")
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido en el cuerpo de la solicitud"}, status=400)
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return JsonResponse({
            "error": "Error inesperado",
            "details": str(e)
        }, status=500)


@login_required
@require_GET
def payment_success(request):
    # Obtener parámetros de la URL
    payment_data = {
        'collection_id': request.GET.get('collection_id'),
        'collection_status': request.GET.get('collection_status'),
        'payment_id': request.GET.get('payment_id'),
        'status': request.GET.get('status'),
        'external_reference': request.GET.get('external_reference'),
        'payment_type': request.GET.get('payment_type'),
        'merchant_order_id': request.GET.get('merchant_order_id'),
        'preference_id': request.GET.get('preference_id'),
        'site_id': request.GET.get('site_id'),
        'processing_mode': request.GET.get('processing_mode'),
        'merchant_account_id': request.GET.get('merchant_account_id'),
    }

    if not all([payment_data['collection_id'], payment_data['status'], payment_data['external_reference'], payment_data['payment_id']]):
        return HttpResponseBadRequest("Parámetros faltantes en la URL")

    if payment_data['status'] != 'approved':
        logger.warning(f"Pago no aprobado. Estado: {payment_data['status']}")
        print(' no se puede continuar'. payment_data)
        return render(request, 'payment_error.html', {'error': 'El pago no fue aprobado', 'url_front': f"{settings.FRONTEND_URL}/pricing"})

    try:
        user = get_object_or_404(User, id=payment_data['external_reference'])
        subscriptions = Subscription.objects.filter(user=user, preference_id=payment_data['preference_id'], active=False)

        if not subscriptions.exists():
            logger.error(f"No se encontraron suscripciones inactivas para el usuario {payment_data['external_reference']} con preference_id {payment_data['preference_id']}")
            return render(request, 'payment_error.html', {'error': 'No se encontraron suscripciones válidas', 'url_front': f"{settings.FRONTEND_URL}/pricing"})

        for subscription in subscriptions:
            # Actualizar el estado de la suscripción
            subscription.active = True
            
            # Actualizar campos adicionales
            for key, value in payment_data.items():
                setattr(subscription, key, value)

            subscription.save()

            logger.info(f"Suscripción activada para el usuario {user.id}. Plan: {subscription.plan.name}, Válida hasta: {subscription.end_date}")

        return render(request, 'payment_success.html', {
            'user': user,
            'subscriptions': subscriptions,
            'url_front': f"{settings.FRONTEND_URL}/"
        })

    except Exception as e:
        logger.error(f"Error al procesar el pago exitoso: {str(e)}")
        return render(request, 'payment_error.html', {'error': 'Ocurrió un error al procesar el pago', 'url_front': f"{settings.FRONTEND_URL}/pricing"})

@login_required
@require_GET
def payment_failure(request):
    return render(request, 'payment_failure.html', {
        'url_front': f"{settings.FRONTEND_URL}/pricing"
    })


@api_view(['GET'])
def pricing(request):
    plans = SubscriptionPlan.objects.all().values('name', 'description', 'price', 'duration_days')
    return Response(list(plans))

@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    try:
        payload = json.loads(request.body)
        logger.info(f"Notificación recibida de Mercado Pago: {payload}")

        if payload.get('type') == 'payment':
            payment_id = payload.get('data', {}).get('id')
            if payment_id:
                payment_info = sdk.payment().get(payment_id)
                if payment_info.get('status') == 200:
                    payment_data = payment_info.get('response', {})
                    status = payment_data.get('status')
                    external_reference = payment_data.get('external_reference')

                    if status == 'approved' and external_reference:
                        subscription = Subscription.objects.filter(user__id=external_reference, active=False).first()
                        if subscription:
                            subscription.active = True
                            subscription.payment_id = payment_id
                            subscription.status = status
                            subscription.payment_type = payment_data.get('payment_type_id')
                            subscription.merchant_order_id = payment_data.get('order', {}).get('id')
                            subscription.save()

                            logger.info(f"Suscripción activada para el usuario {external_reference}")
                        else:
                            logger.warning(f"No se encontró suscripción inactiva para el usuario {external_reference}")
                    else:
                        logger.info(f"Pago no aprobado o sin referencia externa. Estado: {status}")
                else:
                    logger.error(f"Error al obtener información del pago {payment_id}")
            else:
                logger.warning("ID de pago no proporcionado en la notificación")
        else:
            logger.info(f"Tipo de notificación no manejada: {payload.get('type')}")

        return HttpResponse(status=200)
    except json.JSONDecodeError:
        logger.error("Error al decodificar el JSON de la notificación")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error al procesar la notificación: {str(e)}")
        return HttpResponse(status=500)

