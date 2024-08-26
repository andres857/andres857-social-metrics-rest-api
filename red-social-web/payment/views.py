from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
# Mercado Pago SDK
import mercadopago
# Add Your credentials
sdk = mercadopago.SDK("TEST-2257382645000907-082609-b944241f78735358b13ef72bca5af650-147076003")

@csrf_exempt
def create_order_t(request):
    print("Creating order")
    preference_data = {
        "items": [
            {
                "title": "Item 1",
                "quantity": 1,
                "unit_price": 2500
            }
        ]
    }
    preference_response = sdk.preference().create(preference_data)
    print(preference_response)
    preference = preference_response["response"]
    return preference
