import os
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse


# Mercado Pago SDK
import mercadopago
# Add Your credentials

MEI_TOKEN =  os.environ.get('MEI_TOKEN')
sdk = mercadopago.SDK(MEI_TOKEN)

@csrf_exempt
def create_order_t(request):
    print("Creating order")
    preference_data = {
        "items": [
            {
                "title": "Acceso a estadisticas",
                "quantity": 1,
                "unit_price": 200
            }
        ]
    }
    preference_response = sdk.preference().create(preference_data)
    print(preference_response)
    preference = preference_response["response"]
    return JsonResponse(preference, status=201)

