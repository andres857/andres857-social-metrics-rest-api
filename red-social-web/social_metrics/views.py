import pandas as pd
import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Prefetch
from django.core.serializers import serialize


from .models import Institution, SocialNetwork, TypeInstitution, BaseMetrics
from datetime import datetime
from tabulate import tabulate

# return render(request, 'uploadfile.html', {"excel_data":excel_data})
pd.set_option('display.max_columns', 5)  # Muestra hasta 20 columnas


def get_all_institutions(request):
    return HttpResponse("Hello, world. Institutions")

def uploadFile(request):
    return render(request, 'uploadfile.html')

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
    
@csrf_exempt
def create_institution(request):
    if request.method == 'POST':
        try:
            # Parsear el JSON del cuerpo de la solicitud
            data = json.loads(request.body)
            
            # Extraer los datos
            nombre = data.get('nombre')
            ciudad = data.get('ciudad')
            tipo = data.get('tipo')
            url = data.get('url')
            
            with transaction.atomic():
                try:
                    tipo_institucion = TypeInstitution.objects.get(name=tipo)
                except TypeInstitution.DoesNotExist:
                    print("11222")
                    # Si no existe, crear uno nuevo
                    tipo_institucion = TypeInstitution.objects.create(name=tipo, url=url)

                institution = Institution(
                    name=nombre,
                    city=ciudad,
                    type_institution=tipo_institucion
                )
                institution.save()

                response_data = {
                    'status': 'success',
                    'message': 'Institución creada correctamente',
                    'data': {
                        'id': institution.id,
                        'nombre': institution.name,
                        'ciudad': institution.city,
                        'tipo': {
                            'id': tipo_institucion.id,
                            'nombre': tipo_institucion.name,
                            'url': tipo_institucion.url
                        }
                    }
                }

            return JsonResponse(response_data, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@csrf_exempt
def create_metrics(request):
    if request.method == 'POST':
        try:
            # Parsear el JSON del cuerpo de la solicitud
            data = json.loads(request.body)
            
            # Extraer los datos
            followers = data.get('followers')
            publications = data.get('publications')
            reactions = data.get('reactions')
            date_collection = data.get('date_collection')
            institution_id = data.get('institution_id')
            socialnetwork_id = data.get('social_network_id')

            with transaction.atomic():
                metrics = BaseMetrics(
                    followers=followers,
                    publications=publications,
                    reactions=reactions,
                    date_collection=date_collection,
                    institution_id= institution_id,
                    socialnetwork_id= socialnetwork_id
                )
                metrics.save()

                response_data = {
                    'status': 'success',
                    'message': 'Institución creada correctamente',
                    'data': {
                        "followers": metrics.followers,
                        "publications": metrics.publications,
                        "reactions": metrics.reactions,
                        "date_collection": metrics.date_collection,
                        "institution_id": metrics.institution_id,
                        "social_network_id": metrics.socialnetwork_id
                    }
                }

            return JsonResponse(response_data, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)  
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    
""""
funciones para crear los registros desde el archivo excel
"""
def create_or_get_institution_from_excel( name , city, type_institution):
    url = 'http://test.image'        
    with transaction.atomic():
        try:
            tipo_institucion = TypeInstitution.objects.get(name=type_institution)
        except TypeInstitution.DoesNotExist:
            print("11222")
            # Si no existe, crear uno nuevo
            tipo_institucion = TypeInstitution.objects.create(name=type_institution, url=url)

        institution = Institution(
            name=name,
            city=city,
            type_institution=tipo_institucion
        )
        institution.save()
        print(institution)
        return institution.id 

def create_metrics_from_excel(followers,publications,reactions,date_collection,institution_id, socialnetwork_id):
    
    with transaction.atomic():
        metrics = BaseMetrics(
            followers=followers,
            publications=publications,
            reactions=reactions,
            date_collection=date_collection,
            institution_id= institution_id,
            socialnetwork_id= socialnetwork_id
        )
        metrics.save()
        
""""
funciones para crear los registros desde el archivo excel
"""

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
            
            # Leer datos de la pestaña
            df = pd.read_excel(xls, sheet_name=nombre_pestana, skiprows=1)
            print("\nDatos de la pestaña:")
            print(tabulate(df, headers='keys', tablefmt='psql'))

            for index, row in df.iterrows():

                name_institution = row.iloc[0]
                city = row.iloc[1]
                type_institution = row.iloc[2]
                
                institution_id = create_or_get_institution_from_excel(name_institution, city, type_institution);

                followers_facebook = row.iloc[3]
                publications_facebook = row.iloc[4]    
                interactions_facebook = row.iloc[5]    
                # for faceboook
                create_metrics_from_excel(followers_facebook, publications_facebook, interactions_facebook, fecha_recoleccion, institution_id, 1)

                followers_X = row.iloc[6]    
                publications_X = row.iloc[7]    
                interactions_X = row.iloc[8] 
                # for twitter
                create_metrics_from_excel(followers_X, publications_X, interactions_facebook, fecha_recoleccion, institution_id, 3)

                followers_instagram = row.iloc[9]    
                publications_instagram = row.iloc[10]    
                interactions_instagram = row.iloc[11]    
                
                # for instagram
                create_metrics_from_excel(followers_instagram, publications_instagram, interactions_instagram, fecha_recoleccion, institution_id, 4)

                followers_yt = row.iloc[12]    
                publications_yt = row.iloc[13]    
                interactions_yt = row.iloc[14]

                # for youtube
                create_metrics_from_excel(followers_yt, publications_yt, interactions_yt, fecha_recoleccion, institution_id, 5)

                followers_tiktok = row.iloc[15]    
                publications_tiktok = row.iloc[16]    
                interactions_tiktok = row.iloc[17]  

                # for tiktok
                create_metrics_from_excel(followers_instagram, publications_instagram, interactions_instagram, fecha_recoleccion, institution_id, 7)

                print(f"Índice: {index}")
                print(f"Institución: {name_institution}")
                print(f"Ciudad: {city}")
                print(f"Tipo: {type_institution}")
                print(f"Followers Facebook: {followers_facebook}")
                print(f"Publications Facebook: {publications_facebook}")
                print(f"Interactions Facebook: {interactions_facebook}")
                print(f"Followers X: {followers_X}")
                print(f"Publications X: {publications_X}")
                print(f"Interactions X: {interactions_X}")
                print(f"Followers Instagram: {followers_instagram}")
                print(f"Publications Instagram: {publications_instagram}")
                print(f"Interactions Instagram: {interactions_instagram}")
                print(f"Followers YouTube: {followers_yt}")
                print(f"Publications YouTube: {publications_yt}")
                print(f"Interactions YouTube: {interactions_yt}")
                print(f"Followers TikTok: {followers_tiktok}")
                print(f"Publications TikTok: {publications_tiktok}")
                print(f"Interactions TikTok: {interactions_tiktok}")
                print("--------")
                print("--------")

def calcular_engagement_rate(likes, seguidores):
    return (likes / seguidores * 100) if seguidores > 0 else 0

# Consultas
def get_name_institution_by_id(id):
    institution = get_object_or_404(Institution, id=id)
    return institution.name

def get_name_social_network_by_id(id):
    social_network = get_object_or_404(SocialNetwork, id=id)
    return social_network.name

def get_social_metrics(request):
    # Obtener el parámetro 'type' de la URL
    institution_type = request.GET.get('type')
    
    if not institution_type:
        return JsonResponse({"error": "Tipo de institución no especificado"}, status=400)
    
    try:
        # Obtener el tipo de institución
        type_obj = TypeInstitution.objects.get(name=institution_type)
        
        # Filtrar las métricas basadas en el tipo de institución
        metrics = BaseMetrics.objects.filter(
            institution__type_institution=type_obj
        ).select_related('institution', 'socialnetwork')
        
        # Serializar el QuerySet a JSON
        metrics_json = serialize('json', metrics, 
                                 use_natural_foreign_keys=True, 
                                 use_natural_primary_keys=True)
        
        # Convertir la cadena JSON a una lista de diccionarios
        metrics_list = json.loads(metrics_json)
        
        # Extraer solo los campos necesarios
        data = []
        print(metrics_list)
        for item in metrics_list:
            metric = item['fields']
            name_institution = get_name_institution_by_id(metric['institution'])
            name_social_network = get_name_social_network_by_id(metric['socialnetwork'])
            data.append({
                "institution": name_institution,
                "social_network": name_social_network,
                "followers": metric['followers'],
                "publications": metric['publications'],
                "reactions": metric['reactions'],
                "date_collection": metric['date_collection'],
                "engagement_rate": metric['engagment_rate']
            })
        
        return JsonResponse({"metrics": data})
    
    except TypeInstitution.DoesNotExist:
        return JsonResponse({"error": f"Tipo de institución '{institution_type}' no encontrado"}, status=404)