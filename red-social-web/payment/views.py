import os
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseBadRequest

from django.conf import settings

from .serializers import SubscriptionPlanSerializer, PaymentTokenDiscountSerializer

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework import status

from datetime import datetime, timedelta
import secrets

from dateutil.relativedelta import relativedelta
import json
import logging
logger = logging.getLogger(__name__)

from .models import Subscription, SubscriptionPlan, PaymentTokenDiscount

# Mercado Pago SDK
import mercadopago
# Add Your credentials
User = get_user_model()
MEI_TOKEN = os.environ.get('MEI_TOKEN')
sdk = mercadopago.SDK(MEI_TOKEN)
ADMIN_ROLE_IDENTIFIERS = ['8np49Ab#', 'Ca0-T17A']


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

        # Verificar si el usuario ya tiene suscripciones activas para los planes solicitados
        existing_subscriptions = Subscription.objects.filter(
            user=user,
            active=True,
            plan_id__in=[SubscriptionPlan.objects.get(name=plan_name).id for plan_name in plans]
        )

        if existing_subscriptions.exists():
            existing_plan_names = [sub.plan.name for sub in existing_subscriptions]
            return JsonResponse({
                "error": "Ya existen suscripciones activas para los siguientes planes",
                "existing_plans": existing_plan_names
            }, status=400)

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
                plan_id=plan.id
            )
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
    plans = SubscriptionPlan.objects.all().values('id', 'name', 'description', 'price', 'duration_days', 'title', 'imageCover')
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




def generate_secure_token(length=32):
    # Genera un token aleatorio y seguro de la longitud especificada
    return secrets.token_urlsafe(length)

def create_discount_token(discount, plan_ids, start_date_str, end_date_str, title):
    # Parseamos las fechas de inicio y fin a objetos datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Obtenemos los planes usando sus IDs
    plans = SubscriptionPlan.objects.filter(id__in=plan_ids)

    # Genera un token seguro y único
    token_str = generate_secure_token()

    # Creamos el token de descuento
    discount_token = PaymentTokenDiscount.objects.create(
        token=token_str,
        discount=discount,
        start_date=start_date,
        end_date=end_date,
        title=title
    )

    # Asociamos los planes al token
    discount_token.subscription_plans.set(plans)
    
    return discount_token


@csrf_exempt
@require_POST
def create_token_endpoint(request):
    try:
        data = json.loads(request.body)
        
        print("Data received:", data)  # Depuración

        discount = data.get('discount')
        plan_ids = data.get('plan_ids')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        title = data.get('title')

        print("Discount:", discount)
        print("Plan IDs:", plan_ids)
        print("Start Date:", start_date)
        print("End Date:", end_date)

        if not discount or not plan_ids or not start_date or not end_date:
            return JsonResponse({"error": "Los campos 'discount', 'plan_ids', 'start_date' y 'end_date' son requeridos."}, status=400)

        discount_token = create_discount_token(
            discount=discount,
            plan_ids=plan_ids,
            start_date_str=start_date,
            end_date_str=end_date,
            title=title
        )

        return JsonResponse({
            "success": True,
            "title": discount_token.title,
            "token": discount_token.token,
            "discount": discount_token.discount,
            "start_date": discount_token.start_date,
            "end_date": discount_token.end_date,
            "subscription_plans": [plan.name for plan in discount_token.subscription_plans.all()]
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Formato JSON inválido."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@api_view(['GET'])
def list_tokens_endpoint(request):
    tokens = PaymentTokenDiscount.objects.all()
    serializer = PaymentTokenDiscountSerializer(tokens, many=True)
    return Response({"tokens": serializer.data})

@csrf_exempt
@api_view(['GET'])
def get_token_details(request, token):
    try:
        token_discount = PaymentTokenDiscount.objects.get(token=token)
        # Serializar los planes asociados
        plans = [plan.name for plan in token_discount.subscription_plans.all()]  # Cambiar suscripName por name
        return Response({
            "token": token_discount.token,
            "discount": token_discount.discount,
            "subscription_plans": plans,
        })
    except PaymentTokenDiscount.DoesNotExist:
        return Response({"error": "Token no encontrado"}, status=404)

# @ensure_csrf_cookie
@csrf_exempt
@api_view(['PUT'])
def update_token(request, token):
    print(f"Intentando actualizar token: {token}")
    try:
        token_discount = PaymentTokenDiscount.objects.get(id=token)
    except ObjectDoesNotExist:
        return Response({"error": f"No se encontró ningún token de descuento con el valor '{token}'."}, 
                        status=status.HTTP_404_NOT_FOUND)
    
    # Extraer los datos del request
    data = request.data
    
    # Actualizar los campos simples
    token_discount.title = data.get('title', token_discount.title)
    token_discount.discount = data.get('discount', token_discount.discount)
    token_discount.start_date = data.get('start_date', token_discount.start_date)
    token_discount.end_date = data.get('end_date', token_discount.end_date)
    
    # Actualizar los planes de suscripción
    if 'plan_ids' in data:
        plan_ids = data['plan_ids']
        subscription_plans = SubscriptionPlan.objects.filter(id__in=plan_ids)
        token_discount.subscription_plans.set(subscription_plans)
    
    token_discount.save()
    
    serializer = PaymentTokenDiscountSerializer(token_discount)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
    
@csrf_exempt
@login_required
def delete_token(request, token):
    # Verifica si el usuario tiene los roles necesarios
    user_roles = request.user.user_roles.filter(role__identifier__in=ADMIN_ROLE_IDENTIFIERS)

    if not user_roles.exists():
        raise PermissionDenied("No tienes permiso para realizar esta acción.")
    
    print(f"Token recibido: {token}")  # Debug para ver si el token se está recibiendo correctamente

    try:
        # Busca el token a eliminar
        discount_token = PaymentTokenDiscount.objects.get(id=token)
        discount_token.delete()
        return JsonResponse({"success": True, "message": "Token eliminado correctamente."}, status=200)
    except PaymentTokenDiscount.DoesNotExist:
        print(f"Token no encontrado en la base de datos: {token}")  # Debug para verificar si existe
        return JsonResponse({"error": "Token no encontrado."}, status=404)
    
    
@api_view(['GET', 'POST'])
def subscription_plan_list_create(request):
    if request.method == 'GET':
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def subscription_plan_detail(request, pk):
    try:
        plan = SubscriptionPlan.objects.get(pk=pk)
    except SubscriptionPlan.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SubscriptionPlanSerializer(plan)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SubscriptionPlanSerializer(plan, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)