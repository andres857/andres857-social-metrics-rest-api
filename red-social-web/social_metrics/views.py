from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Institution, SocialNetwork

import pandas as pd
from datetime import datetime
import json


# return render(request, 'uploadfile.html', {"excel_data":excel_data})

def get_all_institutions(request):
    return HttpResponse("Hello, world. Institutions")

def uploadFile(request):
    return render(request, 'uploadfile.html')

def createInstitutionsRecordsFromFile(df_institutions):
    name_columns = ["Institucion","Ciudad","Tipo"]
    pass

@csrf_exempt
def process_institution(request):
    if request.method == 'POST':
        try:
            # Parsear el JSON del cuerpo de la solicitud
            data = json.loads(request.body)
            
            # Extraer los datos
            nombre = data.get('nombre')
            ciudad = data.get('ciudad')
            tipo = data.get('tipo')
            
            # Crear el registro en la base de datos
            with transaction.atomic():
                institution = Institution(
                    name=nombre,
                    city=ciudad,
                    type=tipo
                )
                institution.save()

            response_data = {
                'status': 'success',
                'message': 'Institución creada correctamente',
                'data': {
                    'id': institution.id,
                    'nombre': institution.name,
                    'ciudad': institution.city,
                    'tipo': institution.type
                }
            }

            return JsonResponse(response_data, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    
@csrf_exempt
def create_social_network(request):
    if request.method == 'POST':
        try:
            # Parsear el JSON del cuerpo de la solicitud
            data = json.loads(request.body)
            
            # Extraer los datos
            nombre = data.get('nombre')
            
            # Crear el registro en la base de datos
            with transaction.atomic():
                social_network = SocialNetwork(
                    name=nombre,
                )
                social_network.save()

            response_data = {
                'status': 'success',
                'message': 'Institución creada correctamente',
                'data': {
                    'id': social_network.id,
                    'nombre': social_network.name
                }
            }

            return JsonResponse(response_data, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def convertir_nombre_pestana_a_fecha(nombre_pestana):
    # Asumiendo que el nombre de la pestaña está en formato 'YYYY-MM'
    return datetime.strptime(nombre_pestana, '%Y-%m')

def procesar_datos_excel(request):
    if "GET" == request.method:
        return render(request, 'uploadfile.html', {})
    else:
        excel_file = request.FILES["excel_file"]

        xls = pd.ExcelFile(excel_file)
        
        for nombre_pestana in xls.sheet_names:
            fecha_recoleccion = convertir_nombre_pestana_a_fecha(nombre_pestana)
            print(f"\nProcesando datos para el período: {nombre_pestana}")
            print(f"Fecha de recolección: {fecha_recoleccion}")
            columns = ["Institucion","Ciudad","Tipo"]
            
            # Leer datos de la pestaña
            df = pd.read_excel(xls, sheet_name=nombre_pestana)
            institucions_df = df.iloc[:, :3]
            print("\nDatos de la pestaña:")
            print(institucions_df)

            for index, row in institucions_df.iterrows():
                if row is not None:
                    # print(f"Nombre: {row['Institucion']}, Edad: {row['Ciudad']}, Ciudad: {row['Tipo']}")
                    print(row)

            # print("\nEstadísticas resumidas:")
            # print(df.describe())
            
            # print("\nCálculo de engagement rate para cada fila:")
            # for _, row in df.iterrows():
            #     engagement_rate = calcular_engagement_rate(row['likes'], row['seguidores'])
            #     print(f"Institución ID: {row['institucion_id']}, Red Social ID: {row['red_social_id']}, Engagement Rate: {engagement_rate:.2f}%")

def calcular_engagement_rate(likes, seguidores):
    return (likes / seguidores * 100) if seguidores > 0 else 0
