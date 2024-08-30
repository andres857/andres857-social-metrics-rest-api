import pandas as pd
import json, os, requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q, F
from django.core.serializers import serialize
from django.conf import settings
from collections import defaultdict
from datetime import date
from .models import Institution, SocialNetwork, TypeInstitution, InstitutionStatsByType
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
def convertir_nombre_pestana_a_fecha(nombre_pestana):
    # Asumiendo que el nombre de la pestaña está en formato 'YYYY-MM'
    return datetime.strptime(nombre_pestana, '%Y-%m')

def create_or_get_institution_from_excel( name , city, type_institution):
    url = 'http://test.image'        
    with transaction.atomic():
        # crear el tipo de institution
        try:
            tipo_institucion = TypeInstitution.objects.get(name=type_institution)
        except TypeInstitution.DoesNotExist:
            print("11222")
            # Si no existe, crear uno nuevo
            tipo_institucion = TypeInstitution.objects.create(name=type_institution, url=url)
        
        # crear la institution
        try:
            institution = Institution.objects.get(name=name)
        except Institution.DoesNotExist:
            institution = Institution.objects.create(
                name=name,
                city=city,
                type_institution=tipo_institucion
            )
            # institution.save()
            # print(institution)
        return institution.id 

def create_metrics_from_excel(followers,publications,reactions,date_collection,institution_id, socialnetwork_id):
    # Validación y seteo a 0 para métricas no proporcionadas o NaN
    followers = 0 if pd.isna(followers) else max(0, float(followers))
    publications = 0 if pd.isna(publications) else max(0, float(publications))
    reactions = 0 if pd.isna(reactions) else max(0, float(reactions))

    # Cálculo de average_views
    if publications > 0:
        average_views = reactions / publications
    else:
        average_views = 0  # o podrías usar None si prefieres indicar que no se puede calcular

    try:
        with transaction.atomic():
            metrics = BaseMetrics(
                followers=followers,
                publications=publications,
                reactions=reactions,
                Average_views=average_views,
                date_collection=date_collection,
                institution_id= institution_id,
                socialnetwork_id= socialnetwork_id
            )
            metrics.save()
    except Exception as e:
        # Capturar cualquier otra excepción no prevista
        raise ValueError(f"Error inesperado al crear las métricas: {str(e)}, {socialnetwork_id}")

def get_channel_stats_youtube(channel):
    api_key = settings.YOUTUBE_API_KEY

    if not api_key:
        raise ValueError(f"API key YOUTUBE no configurada")
    if pd.isna(channel) or channel == '' or channel is None:
        return {
            'subscriber_count': 0,
            'views': 0,
            'video_count': 0,
        }
    base_url = 'https://www.googleapis.com/youtube/v3/channels'
    
    # Determinar si es un ID de canal o un nombre de usuario/handle
    if channel.startswith('UC'):
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': channel,
            'key': api_key
        }
    else:
        # Si comienza con @, quitamos el @ para la búsqueda
        if channel.startswith('@'):
            channel = channel[1:]
        params = {
            'part': 'snippet,contentDetails,statistics',
            'forUsername': channel,
            'key': api_key
        }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get('items'):
            # Si no se encuentra el canal por username, intentamos buscar por handle
            if 'forUsername' in params:
                params = {
                    'part': 'snippet,contentDetails,statistics',
                    'forHandle': f'@{channel}',
                    'key': api_key
                }
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()

            if not data.get('items'):
                # return JsonResponse({'error': 'No se encontró el canal'}, status=404)
                raise ValueError(f"No se encontró el canal: {str(e)}")

        channel_info = data['items'][0]
        statistics = channel_info['statistics']
        print("FUNCTION STATS YOUTUBE")

        # return JsonResponse({
        #     'subscriber_count': statistics.get('subscriberCount', 'N/A'),
        #     'view_count': statistics['viewCount'],
        #     'video_count': statistics['videoCount'],
        # })
        return {
            'subscriber_count': statistics.get('subscriberCount', 'N/A'),
            'views': statistics['viewCount'],
            'video_count': statistics['videoCount'],
        }
    except Exception as e:
        # Capturar cualquier otra excepción no prevista
        raise ValueError(f"Error inesperado al crear las métricas YOUTUBE: {str(e)}", channel)

""""
END funciones para crear los registros desde el archivo excel
"""

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
                channel_youtube = row.iloc[1]
                city = row.iloc[2]
                type_institution = row.iloc[3]
                
                institution_id = create_or_get_institution_from_excel(name_institution, city, type_institution);
                print("instituion id: ",institution_id)
                followers_facebook = row.iloc[4]
                publications_facebook = row.iloc[5]    
                interactions_facebook = row.iloc[6]    
                print(followers_facebook,publications_facebook,interactions_facebook,interactions_facebook)
                
                # for faceboook
                create_metrics_from_excel(followers_facebook, publications_facebook, interactions_facebook, fecha_recoleccion, institution_id, 1)

                followers_X = row.iloc[7]    
                publications_X = row.iloc[8]    
                interactions_X = row.iloc[9] 
                print(f"Followers Facebook: {followers_facebook}")
                
                # for twitter
                create_metrics_from_excel(followers_X, publications_X, interactions_facebook, fecha_recoleccion, institution_id, 3)

                followers_instagram = row.iloc[10]    
                publications_instagram = row.iloc[11]    
                interactions_instagram = row.iloc[12]    
                
                # for instagram
                create_metrics_from_excel(followers_instagram, publications_instagram, interactions_instagram, fecha_recoleccion, institution_id, 4)

                followers_yt = row.iloc[13]    
                publications_yt = row.iloc[14]    
                interactions_yt = row.iloc[15]

                # for youtube
                stats_youtube = get_channel_stats_youtube(channel_youtube)
                print("--------------------------------")
                print(stats_youtube)
                create_metrics_from_excel(stats_youtube["subscriber_count"], stats_youtube["video_count"], stats_youtube["views"], fecha_recoleccion, institution_id, 5)

                followers_tiktok = row.iloc[16]    
                publications_tiktok = row.iloc[17]    
                interactions_tiktok = row.iloc[18]  

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
def get_data_from_institution_by_id(id):
    institution = get_object_or_404(Institution, id=id)
    return institution

def get_type_institution(id):
    type_institution = get_object_or_404(TypeInstitution, id=id)
    return type_institution

def get_name_social_network_by_id(id):
    social_network = get_object_or_404(SocialNetwork, id=id)
    return social_network.name

def transform_data(metrics):
    institutions = {}

    for metric in metrics:
        institution_name = metric["institution"]
        social_network = metric["social_network"]
        city = metric["city"]
        type_institution = metric["type"]

        if institution_name not in institutions:
            institutions[institution_name] = {
                "Institucion": institution_name,
                "Ciudad": city,
                "Tipo": type_institution,
                "social_networks": {
                    "Facebook": {"followers": 0, "publications": 0, "reactions": 0, "engagement": None},
                    "Instagram": {"followers": 0, "publications": 0, "reactions": 0, "engagement": None},
                    "Tiktok": {"followers": 0, "publications": 0, "reactions": 0, "engagement": None},
                    "X": {"followers": 0, "publications": 0, "reactions": 0, "engagement": None},
                    "YouTube": {"followers": 0, "publications": 0, "reactions": 0, "engagement": None}
                }
            }
        
        institutions[institution_name]["social_networks"][social_network].update({
            "followers": metric["followers"],
            "publications": metric["publications"],
            "reactions": metric["reactions"],
            "engagement": metric["engagement_rate"]
        })

    # Convertir el diccionario de instituciones a una lista
    institutions_list = list(institutions.values())

    # Crear la estructura final
    result = {"metrics": institutions_list}
    return result

def manage_social_metrics(request):

    institution_type = request.GET.get('type')
    print(institution_type, date)

    if institution_type == "todos":
        return get_metrics_by_date(request)
        # return get_all_institutions()
        # return JsonResponse({"error": "Tipo de institución no especificado"}, status=400)
    
    # return get_institutions_from_type(institution_type)
    # return get_metrics_by_date(date(2020, 12, 1))
    # return get_metrics_by_date(date_obj)
    return get_metrics_by_type_and_date(request)

def get_institutions_from_type(institution_type):
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
            institution = get_data_from_institution_by_id(metric['institution']) 
            type_institution = get_type_institution(institution.type_institution_id)
            name_social_network = get_name_social_network_by_id(metric['socialnetwork'])
            data.append({
                "institution": institution.name,
                "type": type_institution.name,
                "city": institution.city,
                "social_network": name_social_network,
                "followers": metric['followers'],
                "publications": metric['publications'],
                "reactions": metric['reactions'],
                "date_collection": metric['date_collection'],
                "engagement_rate": metric['engagment_rate']
            })

        transformed_data = transform_data(data)
        print(transformed_data)
        return JsonResponse(transformed_data)

    except TypeInstitution.DoesNotExist:
        return JsonResponse({"error": f"Tipo de institución '{institution_type}' no encontrado"}, status=404)

def get_metrics_by_date(request):
    date_str = request.GET.get('date')
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    print(target_date)
    try:
        # Filtrar las métricas por la fecha específica
        metrics = BaseMetrics.objects.filter(date_collection=target_date).select_related('institution', 'socialnetwork')
        
        # Serializar el QuerySet a JSON
        metrics_json = serialize('json', metrics, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        
        # Convertir la cadena JSON a una lista de diccionarios
        metrics_list = json.loads(metrics_json)
        
        # Procesar y transformar los datos como antes
        data = []
        for item in metrics_list:
            metric = item['fields']
            institution = get_data_from_institution_by_id(metric['institution'])
            type_institution = get_type_institution(institution.type_institution_id)
            name_social_network = get_name_social_network_by_id(metric['socialnetwork'])
            
            data.append({
                "institution": institution.name,
                "type": type_institution.name,
                "city": institution.city,
                "social_network": name_social_network,
                "followers": metric['followers'],
                "publications": metric['publications'],
                "reactions": metric['reactions'],
                "date_collection": metric['date_collection'],
                "engagement_rate": metric['engagment_rate']
            })
        
        transformed_data = transform_data(data)
        
        return JsonResponse(transformed_data, safe=False)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def get_metrics_by_type_and_date(request):
    try:
        # Obtener los parámetros de la URL
        institution_type = request.GET.get('type')
        date_str = request.GET.get('date')

        # Convertir la fecha de string a objeto date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

        # Construir el filtro
        filter_conditions = Q()
        if institution_type:
            filter_conditions &= Q(institution__type_institution__name=institution_type)
        if target_date:
            filter_conditions &= Q(date_collection=target_date)

        # Aplicar los filtros
        metrics = BaseMetrics.objects.filter(filter_conditions).select_related('institution', 'socialnetwork')

        # Serializar el QuerySet a JSON
        metrics_json = serialize('json', metrics, use_natural_foreign_keys=True, use_natural_primary_keys=True)

        # Convertir la cadena JSON a una lista de diccionarios
        metrics_list = json.loads(metrics_json)

        # Procesar y transformar los datos
        data = []
        for item in metrics_list:
            metric = item['fields']
            institution = get_data_from_institution_by_id(metric['institution'])
            type_institution = get_type_institution(institution.type_institution_id)
            name_social_network = get_name_social_network_by_id(metric['socialnetwork'])

            data.append({
                "institution": institution.name,
                "type": type_institution.name,
                "city": institution.city,
                "social_network": name_social_network,
                "followers": metric['followers'],
                "publications": metric['publications'],
                "reactions": metric['reactions'],
                "date_collection": metric['date_collection'],
                "engagement_rate": metric['engagment_rate']
            })

        transformed_data = transform_data(data)

        return JsonResponse(transformed_data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# function for API request handling
def get_channel_stats_youtube_api_function(request):
    query = request.GET.get('channel', '')
    print("Channel", query)
    api_key = settings.YOUTUBE_API_KEY

    if not api_key:
        return JsonResponse({'error': 'API key no configurada'}, status=500)

    base_url = 'https://www.googleapis.com/youtube/v3/channels'
    
    # Determinar si es un ID de canal o un nombre de usuario/handle
    if query.startswith('UC'):
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': query,
            'key': api_key
        }
    else:
        # Si comienza con @, quitamos el @ para la búsqueda
        if query.startswith('@'):
            query = query[1:]
        params = {
            'part': 'snippet,contentDetails,statistics',
            'forUsername': query,
            'key': api_key
        }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Esto levantará una excepción para códigos de estado no exitosos
        data = response.json()

        if not data.get('items'):
            # Si no se encuentra el canal por username, intentamos buscar por handle
            if 'forUsername' in params:
                params = {
                    'part': 'snippet,contentDetails,statistics',
                    'forHandle': f'@{query}',
                    'key': api_key
                }
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()

            if not data.get('items'):
                return JsonResponse({'error': 'No se encontró el canal'}, status=404)

        channel_info = data['items'][0]
        statistics = channel_info['statistics']
        print (statistics)
        print('--------------------------------')
        print (channel_info)

        return JsonResponse({
            'channel_name': channel_info['snippet']['title'],
            'description': channel_info['snippet']['description'],
            'subscriber_count': statistics.get('subscriberCount', 'N/A'),
            'view_count': statistics['viewCount'],
            'video_count': statistics['videoCount'],
            'playlist_id': channel_info['contentDetails']['relatedPlaylists']['uploads'],
            'thumbnail_url': channel_info['snippet']['thumbnails']['default']['url']
        })

    except requests.RequestException as e:
        return JsonResponse({'error': f'Error al conectar con la API de YouTube: {str(e)}'}, status=500)
    except KeyError as e:
        return JsonResponse({'error': f'Error al procesar la respuesta de la API: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)
    
@csrf_exempt
def bulk_channel_stats(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No se proporcionó ningún archivo'}, status=400)

    file = request.FILES['file']
    
    try:
        df = pd.read_excel(file)
    except Exception as e:
        return JsonResponse({'error': f'Error al leer el archivo Excel: {str(e)}'}, status=400)

    if 'handle' not in df.columns:
        return JsonResponse({'error': 'El archivo no contiene una columna "handle"'}, status=400)

    results = []
    for handle in df['handle']:
        try:
            # Simulamos una solicitud GET con el handle
            fake_request = type('FakeRequest', (), {'GET': {'query': handle}})()
            response = get_channel_stats_youtube(fake_request)
            
            # JsonResponse ya contiene los datos en formato JSON, no necesitamos llamar .json()
            channel_data = response.content
            # Decodificamos los bytes a un diccionario de Python
            channel_data = json.loads(channel_data.decode('utf-8'))
            results.append(channel_data)
        except Exception as e:
            results.append({'handle': handle, 'error': str(e)})

    return JsonResponse({'channels': results})


def create_institution_stats(request):
    try:
        type_institution_id = request.data.get('type_institution_id')
        social_network_id = request.data.get('social_network_id')
        stats_date = request.data.get('stats_date')
        total_followers = request.data.get('total_followers')
        total_publications = request.data.get('total_publications')
        total_reactions = request.data.get('total_reactions')
        average_views = request.data.get('average_views')
        institution_count = request.data.get('institution_count')

        # Convertir la fecha de string a objeto date
        stats_date = datetime.strptime(stats_date, "%Y-%m-%d").date()

        # Obtener las instancias de TypeInstitution y SocialNetwork
        type_institution = get_object_or_404(TypeInstitution, id=type_institution_id)
        social_network = get_object_or_404(SocialNetwork, id=social_network_id)

        # Crear el nuevo registro
        stats = InstitutionStatsByType.objects.create(
            type_institution=type_institution,
            social_network=social_network,
            stats_date=stats_date,
            total_followers=total_followers,
            total_publications=total_publications,
            total_reactions=total_reactions,
            average_views=average_views,
            institution_count=institution_count
        )

        return Response({
            "message": "Estadísticas creadas con éxito",
            "id": stats.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
def get_institution_stats(request):
    try:
        type_institution_id = request.query_params.get('type_institution_id')
        social_network_id = request.query_params.get('social_network_id')
        stats_date = request.query_params.get('stats_date')

        # Validar que todos los parámetros necesarios estén presentes
        if not all([type_institution_id, social_network_id, stats_date]):
            return Response({
                "error": "Faltan parámetros requeridos. Se necesitan type_institution_id, social_network_id y stats_date."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convertir la fecha de string a objeto date
        try:
            stats_date = datetime.strptime(stats_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "error": "Formato de fecha incorrecto. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener las instancias de TypeInstitution y SocialNetwork
        type_institution = get_object_or_404(TypeInstitution, id=type_institution_id)
        social_network = get_object_or_404(SocialNetwork, id=social_network_id)

        # Buscar las estadísticas
        stats = get_object_or_404(InstitutionStatsByType, 
                                  type_institution=type_institution,
                                  social_network=social_network,
                                  stats_date=stats_date)

        # Preparar la respuesta
        response_data = {
            "id": stats.id,
            "type_institution": stats.type_institution.name,
            "social_network": stats.social_network.name,
            "stats_date": stats.stats_date,
            "total_followers": stats.total_followers,
            "total_publications": stats.total_publications,
            "total_reactions": stats.total_reactions,
            "average_views": stats.average_views,
            "institution_count": stats.institution_count,
            "date_updated": stats.date_updated
        }

        return Response(response_data)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

def update_institution_stats(request):
    try:
        # Obtener los parámetros de la solicitud
        type_institution_id = request.data.get('type_institution_id')
        social_network_id = request.data.get('social_network_id')
        stats_date = request.data.get('stats_date')
        followers_increment = request.data.get('followers_increment')
        print(type_institution_id, social_network_id, stats_date, followers_increment)

        # Validar que todos los parámetros necesarios estén presentes
        if not all([type_institution_id, social_network_id, stats_date, followers_increment]):
            return Response({
                "error": "Faltan parámetros requeridos. Se necesitan type_institution_id, social_network_id, stats_date y followers_increment."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convertir la fecha de string a objeto date
        try:
            stats_date = datetime.strptime(stats_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "error": "Formato de fecha incorrecto. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener las instancias de TypeInstitution y SocialNetwork
        type_institution = get_object_or_404(TypeInstitution, id=type_institution_id)
        social_network = get_object_or_404(SocialNetwork, id=social_network_id)

        # Buscar y actualizar las estadísticas
        stats = InstitutionStatsByType.objects.filter(
            type_institution=type_institution,
            social_network=social_network,
            stats_date=stats_date
        )

        if not stats.exists():
            return Response({
                "error": "No se encontraron estadísticas para los parámetros proporcionados."
            }, status=status.HTTP_404_NOT_FOUND)

        # Actualizar incrementalmente el campo total_followers
        stats.update(total_followers=F('total_followers') + followers_increment)

        # Obtener el objeto actualizado
        updated_stats = stats.first()

        # Preparar la respuesta
        response_data = {
            "id": updated_stats.id,
            "type_institution": updated_stats.type_institution.name,
            "social_network": updated_stats.social_network.name,
            "stats_date": updated_stats.stats_date,
            "total_followers": updated_stats.total_followers,
            "total_publications": updated_stats.total_publications,
            "total_reactions": updated_stats.total_reactions,
            "average_views": updated_stats.average_views,
            "institution_count": updated_stats.institution_count,
            "date_updated": updated_stats.date_updated
        }

        return Response(response_data)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET','POST','PUT'])
def manage_stats(request):
    if request.method == 'GET':
        return get_institution_stats(request)
    elif request.method == 'PUT':
        print("hello")
        return update_institution_stats(request)

    # elif request.method == 'POST':
    #     # Crear una nueva estadística
    #     serializer = InstitutionStatsByTypeSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    