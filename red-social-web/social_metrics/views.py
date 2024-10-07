import pandas as pd
import json, os, requests, re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.db import connection
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.db.models import Q, F, Count
from django.db.models.functions import TruncDate
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from collections import defaultdict
from datetime import date
from .models import Institution, SocialNetwork, TypeInstitution, InstitutionStatsByType, BaseMetrics
from datetime import datetime
from tabulate import tabulate
from .serializers import InstitutionSerializer, TypeInstitutionSerializer
from urllib.parse import urlparse, unquote, quote


# return render(request, 'uploadfile.html', {"excel_data":excel_data})
pd.set_option('display.max_columns', 5)  # Muestra hasta 20 columnas

def uploadFile(request):
    return render(request, 'uploadfile.html')

@api_view(['POST', 'PUT'])
def manage_social_networks(request,id):
    if request.method == 'POST':
        return create_social_network(request)
    elif request.method == 'PUT':
        return update_social_network_api(request,id)
    
@csrf_exempt
def create_social_network(request):
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

@csrf_exempt
def update_social_network_api(request, id):
    try:
        # Parsear el JSON del cuerpo de la solicitud
        data = json.loads(request.body)
        
        # Extraer los datos
        percentage_correction_type_institution = data.get('percentage_type_institution')
        percentage_correction_social_network = data.get('percentage_social_network')
        
        # Obtener el registro existente
        try:
            social_network = SocialNetwork.objects.get(id=id)
        except SocialNetwork.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'SocialNetwork no encontrada'}, status=404)
        
        # Actualizar el registro en la base de datos
        with transaction.atomic():
            if percentage_correction_type_institution is not None:
                social_network.percentage_correction_type_institutions = percentage_correction_type_institution
                social_network.percentage_correction_social_networks = percentage_correction_social_network
            social_network.save()

        response_data = {
            'status': 'success',
            'message': 'SocialNetwork actualizada correctamente',
            'data': {
                'id': social_network.id,
                'nombre': social_network.name,
                'percentage_type_institution': social_network.percentage_correction_type_institutions,
                'percentage_social_network': social_network.percentage_correction_social_networks

            }
        }
        return JsonResponse(response_data, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)        

@csrf_exempt
def create_institution(request):
    try:
        # Parsear el JSON del cuerpo de la solicitud
        data = json.loads(request.body)
        
        # Extraer los datos
        nombre = data.get('nombre')
        ciudad = data.get('ciudad')
        tipo = data.get('tipo')
        url = data.get('url')
        
        with transaction.atomic():
            # Primero crea el tipo de institucion 
            try:
                tipo_institucion = TypeInstitution.objects.get(name=tipo)
            except TypeInstitution.DoesNotExist:
                # Si no existe, crear uno nuevo
                tipo_institucion = TypeInstitution.objects.create(
                    name=tipo, 
                    url=url,
                )

            institution, inst_created = Institution.objects.get_or_create(
                name=nombre,
                defaults={
                    'city': ciudad,
                    'type_institution': tipo_institucion
                }
            )
            
            # Si se creó una nueva institución, incrementar el contador
            if inst_created:
                TypeInstitution.objects.filter(id=tipo_institucion.id).update(institution_count=F('institution_count') + 1)
                tipo_institucion.refresh_from_db()

            response_data = {
                'status': 'success',
                'message': 'Institución creada correctamente' if inst_created else 'Institución ya existente',
                'data': {
                    'id': institution.id,
                    'nombre': institution.name,
                    'ciudad': institution.city,
                    'tipo': {
                        'id': tipo_institucion.id,
                        'nombre': tipo_institucion.name,
                        'url': tipo_institucion.url,
                        'institution_count': tipo_institucion.institution_count
                    },
                    'created': inst_created
                }
            }
        return JsonResponse(response_data, status=201 if inst_created else 200)
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)

def list_intitutions_by_type(request):
    category = request.query_params.get('category')
    try:
        # Obtener todas las instituciones
        type_institutions = TypeInstitution.objects.filter(category=category)

        # Serializar los datos
        serializer = TypeInstitutionSerializer(type_institutions, many=True)

        # Devolver la respuesta
        return Response(serializer.data)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
def manage_institutions(request):
    if request.method == 'POST':
        return create_institution(request)

def dates_collections(request):
    try:
        unique_dates = (
            BaseMetrics.objects
            .values('date_collection')
            .annotate(date=F('date_collection'))
            .values('date')
            .distinct()
            .order_by('-date')
        )
        # Para ver los resultados
        for date_entry in unique_dates:
            print(date_entry['date'])
        dates = list(unique_dates)
        return JsonResponse(dates, safe=False, encoder=DjangoJSONEncoder)

    except Exception as e:
        print(e)
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_institutions_for_category_and_date(request):
    category = request.query_params.get('category')
    stats_date = request.query_params.get('stats_date')

    if not category or not stats_date:
        return Response({
            "error": "Both category and stats_date are required."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Validar el formato de la fecha
        datetime.strptime(stats_date, '%Y-%m-%d')
    except ValueError:
        return Response({
            "error": "Invalid date format. Use YYYY-MM-DD."
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    i.type_institution_id,
                    ti.category AS categoria,
                    ti.name,
                    ti.ordering,
                    ti.url,
                    b.date_collection,
                    COUNT(DISTINCT i.id) AS calculated
                FROM
                    social_metrics_institution i
                INNER JOIN
                    social_metrics_typeinstitution ti ON i.type_institution_id = ti.id
                INNER JOIN
                    social_metrics_basemetrics b ON i.id = b.institution_id
                WHERE
                    ti.category = %s
                    AND b.date_collection = %s
                GROUP BY
                    i.type_institution_id, b.date_collection
                ORDER BY
                    i.type_institution_id;
            """, [category, stats_date])
        
            columns = [col[0] for col in cursor.description]
            data = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            for item in data:
                if 'calculated' in item:
                    item['institution_count'] = item.pop('calculated') 

        return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def process_institution_data(data):
    processed = {}
    for item in data:
        institution_id = item['id']
        if institution_id not in processed:
            processed[institution_id] = item
        else:
            # Si ya existe, actualizar solo si la fecha es más reciente
            if item['date_collection'] > processed[institution_id]['date_collection']:
                processed[institution_id] = item
            # Si las fechas son iguales, sumar el conteo
            elif item['date_collection'] == processed[institution_id]['date_collection']:
                processed[institution_id]['sys'] += item['calculated']
    
    return list(processed.values())

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
    return datetime.strptime(nombre_pestana, f'%Y-%m-%d')

def create_or_get_institution_from_excel( name , city, type_institution):
    url = 'http://test.image'
    try:
        with transaction.atomic():
            # crear el tipo de institution
            try:
                tipo_institucion = TypeInstitution.objects.get(name=type_institution)
            except TypeInstitution.DoesNotExist:
                # Si no existe, crear uno nuevo
                try:
                    tipo_institucion = TypeInstitution.objects.create(name=type_institution, url=url)
                except IntegrityError as e:
                    raise ValueError(f"Failed to create TypeInstitution: {type_institution}")
            
            try:
                institution, inst_created = Institution.objects.get_or_create(
                        name=name,
                        defaults={
                            'city': city,
                            'type_institution': tipo_institucion
                        }
                    )
            except IntegrityError as e:
                raise ValueError(f"Failed to create Institution: {name}")
            
            # Si se creó una nueva institución, incrementar el contador
            if inst_created:
                TypeInstitution.objects.filter(id=tipo_institucion.id).update(institution_count=F('institution_count') + 1)
                tipo_institucion.refresh_from_db()

            return institution.id, tipo_institucion.id
        
    except Exception as e:
        raise ValueError(f"Unexpected error creating the institution or typeInstitution: {str(e)}")

def create_metrics_from_excel(followers, publications, reactions, date_collection, institution_id,  id_type_institution, socialnetwork_id):
    # Validación y seteo a 0 para métricas no proporcionadas o NaN
    # print("////////////////", institution_id, socialnetwork_id, "****",followers )
    followers = 0 if pd.isna(followers) else max(0, float(followers))
    publications = 0 if pd.isna(publications) else max(0, float(publications))
    reactions = 0 if pd.isna(reactions) else max(0, float(reactions))

    # Cálculo de average_views
    if publications > 0:
        average_views = round(reactions / publications, 1)
    else:
        average_views = 0

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

        update_institution_stats(id_type_institution, socialnetwork_id, date_collection, followers, publications, reactions)

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
        return {
            'subscriber_count': statistics.get('subscriberCount', 'N/A'),
            'views': statistics['viewCount'],
            'video_count': statistics['videoCount'],
        }
    except Exception as e:
        # Capturar cualquier otra excepción no prevista
        raise ValueError(f"Error inesperado al obtener las métricas de YOUTUBE: {str(e)}", channel)
    
def update_institution_stats(type_institution_id, social_network_id, stats_date,followers_increment, publications_increment, reactions_increment):
    try:
        print("update stats", type_institution_id, social_network_id, stats_date, followers_increment, publications_increment,reactions_increment )
        
        # Obtener las instancias de TypeInstitution y SocialNetwork
        type_institution = get_object_or_404(TypeInstitution, id=type_institution_id)
        social_network = get_object_or_404(SocialNetwork, id=social_network_id)

        print(type_institution, social_network)
        # Buscar y actualizar las estadísticas
        stats, created = InstitutionStatsByType.objects.get_or_create(
            type_institution= type_institution,
            social_network= social_network,
            stats_date= stats_date,
            defaults={
                'total_followers': followers_increment,
                'total_publications': publications_increment,
                'total_reactions': reactions_increment,
            }
        )

        if not created:
            stats.total_followers = F('total_followers') + followers_increment
            stats.total_publications = F('total_publications') + publications_increment
            stats.total_reactions = F('total_reactions') + reactions_increment
            stats.save()

        stats.refresh_from_db()  # Esto es necesario si usaste F() para actualizar
        # print(f"Total de seguidores actual: {stats.total_followers}")

    except Exception as e:
        raise ValueError(f"Error inesperado al crear las stats: {str(e)}")

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
    
            for index, row in df.iterrows():

                name_institution = row.iloc[0]
                channel_youtube = row.iloc[1]
                city = row.iloc[2]
                type_institution = row.iloc[3]
                
                institution_id, id_type_institution  = create_or_get_institution_from_excel(name_institution, city, type_institution);
                print("instituion id: ",institution_id)
                print("---------****************-----")
                print("type_institution id: ",id_type_institution)
                followers_facebook = row.iloc[4]
                publications_facebook = row.iloc[5]
                interactions_facebook = row.iloc[6]    
                
                # for faceboook
                create_metrics_from_excel(followers_facebook, publications_facebook, interactions_facebook, fecha_recoleccion, institution_id, id_type_institution, 1)

                followers_X = row.iloc[7]    
                publications_X = row.iloc[8]    
                interactions_X = row.iloc[9] 
                
                # for twitter
                create_metrics_from_excel(followers_X, publications_X, interactions_facebook, fecha_recoleccion, institution_id,id_type_institution, 3)

                followers_instagram = row.iloc[10]    
                publications_instagram = row.iloc[11]
                interactions_instagram = row.iloc[12]    
                
                # for instagram
                create_metrics_from_excel(followers_instagram, publications_instagram, interactions_instagram, fecha_recoleccion, institution_id,id_type_institution, 4)
                
                # obtiene las estadisticas de la api de youtube si se especifica el user en el file de excel
                #stats_youtube = get_channel_stats_youtube(channel_youtube)
                #create_metrics_from_excel(stats_youtube["subscriber_count"], stats_youtube["video_count"], stats_youtube["views"], fecha_recoleccion, institution_id,id_type_institution, 5)

                print("gets stats from excel file", fecha_recoleccion)
                followers_yt = row.iloc[13]
                publications_yt = row.iloc[14]
                interactions_yt = row.iloc[15]
                create_metrics_from_excel(followers_yt, publications_yt, interactions_yt, fecha_recoleccion, institution_id,id_type_institution, 5)

                followers_tiktok = row.iloc[16]    
                publications_tiktok = row.iloc[17]    
                interactions_tiktok = row.iloc[18]  

                # for tiktok
                create_metrics_from_excel(followers_tiktok, publications_tiktok, interactions_tiktok, fecha_recoleccion, institution_id,id_type_institution, 7)

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
                    "Facebook": {"followers": 0, "publications": 0, "reactions": 0, "Average_views": None},
                    "Instagram": {"followers": 0, "publications": 0, "reactions": 0, "Average_views": None},
                    "Tiktok": {"followers": 0, "publications": 0, "reactions": 0, "Average_views": None},
                    "X": {"followers": 0, "publications": 0, "reactions": 0, "Average_views": None},
                    "YouTube": {"followers": 0, "publications": 0, "reactions": 0, "Average_views": None}
                }
            }
        
        institutions[institution_name]["social_networks"][social_network].update({
            "followers": metric["followers"],
            "publications": metric["publications"],
            "reactions": metric["reactions"],
            "Average_views": metric["Average_views"]
        })

    # Convertir el diccionario de instituciones a una lista
    institutions_list = list(institutions.values())

    # Crear la estructura final
    result = {"metrics": institutions_list}
    return result

@api_view(['GET','POST'])
def manage_social_metrics(request):
    if request.method == 'GET':
        institution_type = request.GET.get('type')
        print(institution_type, date)
        if institution_type == "todos":
            return get_metrics_by_date(request)
        
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
        # print(transformed_data)
        return JsonResponse(transformed_data)

    except TypeInstitution.DoesNotExist:
        return JsonResponse({"error": f"Tipo de institución '{institution_type}' no encontrado"}, status=404)

def get_metrics_by_date(request):
    date_str = request.GET.get('date')
    category = request.GET.get('category')

    target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    print(f"Target date 1: {target_date}")

    try:
        # Filtrar las métricas por la fecha específica
        metrics = BaseMetrics.objects.filter(date_collection=target_date).select_related('institution', 'socialnetwork')
        
        # Si se proporciona una categoría, filtrar por ella
        if category:
            metrics = metrics.filter(institution__type_institution__category=category)

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
                "Average_views": metric['Average_views']
            })
        
        # Transformar los datos
        transformed_data = transform_data(data)

        # Preparar la respuesta
        response_data = {
            "data": {
                "metrics": transformed_data["metrics"]
            }
        }
        
        return JsonResponse(response_data, safe=False)
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Esto imprimirá el traceback completo
        return JsonResponse({"error": str(e)}, status=500)

def get_all_metrics_institutions_by_date_and_category(request):
    date_str = request.GET.get('date')
    category = request.GET.get('category')

    target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    print(f"Target date 1: {target_date}")

    try:
        # Filtrar las métricas por la fecha específica
        metrics = BaseMetrics.objects.filter(date_collection=target_date).select_related('institution', 'socialnetwork')
        
        # Si se proporciona una categoría, filtrar por ella
        if category:
            metrics = metrics.filter(institution__type_institution__category=category)

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
                "Average_views": metric['Average_views']
            })
        
        # Transformar los datos
        transformed_data = transform_data(data)

        # Preparar la respuesta
        response_data = {
            "data": {
                "metrics": transformed_data["metrics"]
            }
        }
        
        return JsonResponse(response_data, safe=False)
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Esto imprimirá el traceback completo
        return JsonResponse({"error": str(e)}, status=500)
    
def get_metrics_by_type_and_date(request):
    try:
        institution_type = request.GET.get('type')
        date_str = request.GET.get('date')

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

        filter_conditions = Q()
        if institution_type:
            filter_conditions &= Q(institution__type_institution__name=institution_type)
        if target_date:
            filter_conditions &= Q(date_collection=target_date)

        # Añadir un orden explícito
        metrics = BaseMetrics.objects.filter(filter_conditions).select_related('institution', 'socialnetwork').order_by('institution__name', 'socialnetwork__name')

        # Agrupar métricas por institución
        grouped_metrics = defaultdict(lambda: {"social_networks": {}})
        for metric in metrics:
            institution = metric.institution
            social_network = metric.socialnetwork.name
            grouped_metrics[institution.name]["Institucion"] = institution.name
            grouped_metrics[institution.name]["Ciudad"] = institution.city
            grouped_metrics[institution.name]["Tipo"] = institution.type_institution.name
            grouped_metrics[institution.name]["social_networks"][social_network] = {
                "followers": metric.followers,
                "publications": metric.publications,
                "reactions": metric.reactions,
                "Average_views": metric.Average_views
            }

        # Convertir el defaultdict a una lista para la paginación
        metrics_list = list(grouped_metrics.values())

        # Crear el paginador
        # paginator = Paginator(metrics_list, items_per_page)

        # try:
        #     metrics_page = paginator.page(page)
        # except PageNotAnInteger:
        #     metrics_page = paginator.page(1)
        # except EmptyPage:
        #     metrics_page = paginator.page(paginator.num_pages)

        response_data = {
            "data": {
                "metrics": metrics_list
                # "metrics": list(metrics_page)
                # "metrics": list(metrics_page)
            },
            # "page": metrics_page.number,
            # "total_pages": paginator.num_pages,
            # "has_next": metrics_page.has_next(),
            # "has_previous": metrics_page.has_previous(),
            # "total_count": len(metrics_list)
        }

        return JsonResponse(response_data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_channel_stats_youtube_api_function(request):
    query = request.GET.get('query', '')
    query_format = quote(query, safe='')  # Safely encode the query
    print("Channell", query)
    api_key = settings.YOUTUBE_API_KEY

    if not api_key:
        return JsonResponse({'error': 'API key no configurada'}, status=500)

    base_url = 'https://www.googleapis.com/youtube/v3/channels'
    search_url = 'https://www.googleapis.com/youtube/v3/search'

    # Función para extraer el nombre del canal de la URL
    def extract_channel_name(url):
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)  # Decode the URL path
        match = re.search(r'/c/(.+)$', path)
        return quote(match.group(1)) if match else None 

    # Determinar el tipo de query y ajustar los parámetros
    if query.startswith('UC'):
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': query,
            'key': api_key
        }
    elif query.startswith('https://www.youtube.com/c/'):
        # channel_name = extract_channel_name(query_format)
        channel_name = 'CruzRojaColombiana100años'
        
        if not channel_name:
            return JsonResponse({'error': 'No se pudo extraer el nombre del canal de la URL'}, status=400)
        
        # Primero, buscar el canal por nombre
        search_params = {
            'part': 'snippet',
            'type': 'channel',
            'q': channel_name,
            'key': api_key
        }
        try:
            search_response = requests.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if not search_data.get('items'):
                return JsonResponse({'error': 'No se encontró el canal 1'}, status=404)
            
            channel_id = search_data['items'][0]['id']['channelId']
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': channel_id,
                'key': api_key
            }
        except requests.RequestException as e:
            return JsonResponse({'error': f'Error al buscar el canal: {str(e)}'}, status=500)
    elif query.startswith('@'):
        query = query[1:]
        params = {
            'part': 'snippet,contentDetails,statistics',
            'forUsername': query,
            'key': api_key
        }
    else:
        return JsonResponse({'error': 'el nombre de usuario no coincide con la estructura esperada por youtube'}, status=400)


    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
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
    print ('Bulk channel stats')
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
            response = get_channel_stats_youtube_api_function(fake_request)
            
            # JsonResponse ya contiene los datos en formato JSON, no necesitamos llamar .json()
            channel_data = response.content
            # Decodificamos los bytes a un diccionario de Python
            channel_data = json.loads(channel_data.decode('utf-8'))
            results.append(channel_data)
        except Exception as e:
            results.append({'handle': handle, 'error': str(e)})

    return JsonResponse({'channels': results})

def create_institution_stats_api(request):
    try:
        type_institution_id = request.data.get('type_institution_id')
        social_network_id = request.data.get('social_network_id')
        stats_date = request.data.get('stats_date')
        total_followers = request.data.get('total_followers')
        total_publications = request.data.get('total_publications')
        total_reactions = request.data.get('total_reactions')
        average_views = request.data.get('average_views')
        institution_count = request.data.get('institution_count')
        stats_date = convertir_nombre_pestana_a_fecha(stats_date)
        # Convertir la fecha de string a objeto date

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

# @transaction.atomic
def create_institution_stats_api_t(request):
    try:
        type_institution_id = request.data.get('type_institution_id')
        social_network_id = request.data.get('social_network_id')
        stats_date = request.data.get('stats_date')
        total_followers = request.data.get('total_followers', 0)
        stats_date = convertir_nombre_pestana_a_fecha(stats_date)
        print(stats_date)
        # Obtener las instancias de TypeInstitution y SocialNetwork
        type_institution = get_object_or_404(TypeInstitution, id=type_institution_id)
        social_network = get_object_or_404(SocialNetwork, id=social_network_id)

        # Intentar obtener un registro existente o crear uno nuevo
        stats, created = InstitutionStatsByType.objects.get_or_create(
            type_institution=type_institution,
            social_network=social_network,
            stats_date=stats_date,
            defaults={
                'total_followers': total_followers,
            }
        )

        if not created:
            stats.total_followers = F('total_followers') + total_followers
            stats.save()

        return Response({
            "message": "Estadísticas creadas o actualizadas con éxito",
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

def get_stats_all_categories_by_date(request):
    try:
        stats_date = request.query_params.get('stats_date')
        category = request.query_params.get('category')

        # Validar que la fecha esté presente
        if not all([stats_date,category ]):
            return Response({
                "error": "Parámetros requeridos stats_date y category"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convertir la fecha de string a objeto date
        try:
            stats_date = datetime.strptime(stats_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "error": "Formato de fecha incorrecto. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener todas los tipos de instituciones y redes sociales
        type_institutions = TypeInstitution.objects.filter(category=category)
        social_networks = SocialNetwork.objects.all()

        # Obtener todas las estadísticas para la fecha dada
        stats = InstitutionStatsByType.objects.filter(
            stats_date=stats_date
        ).select_related('type_institution', 'social_network')

        # Crear un diccionario para almacenar las estadísticas
        stats_dict = {
            (stat.type_institution_id, stat.social_network_id): stat 
            for stat in stats
        }

        # Preparar la respuesta
        response_data = []
        for category in type_institutions:
            for network in social_networks:
                stat = stats_dict.get((category.id, network.id))
                stat_data = {
                    "type_institution": category.name,
                    "social_network": network.name,
                    "stats_date": stats_date,
                    "total_followers": stat.total_followers if stat else 0,
                    "total_publications": stat.total_publications if stat else 0,
                    "total_reactions": stat.total_reactions if stat else 0,
                    "average_views": stat.average_views if stat else 0.0,
                    "date_updated": stat.date_updated if stat else None
                }
                response_data.append(stat_data)

        #aplicar el factor de correccion al tipo de institucion
        for stat in response_data:
            followers = stat['total_followers']
            type_institution = stat['type_institution']
            
            p_correction = TypeInstitution.objects.get(name=type_institution)
            # se evalua adicional la red social de tiktok
            if (stat['social_network'] == 'Tiktok'):
                percentage = 5
                followers = followers - ( followers * percentage / 100)
                stat['total_followers'] = round(followers)
                print('seguidores en tiktok finales', stat['total_followers'] )
            else:
                percentage = p_correction.percentage_correction
                followers = followers - ( followers * percentage / 100)
                stat['total_followers'] = round(followers)

        # aplicar el filtro entre typos de institucion dentro de cada red social
        followers_facebook = 0
        followers_X = 0
        followers_Instagram = 0
        followers_YouTube = 0
        followers_Tiktok = 0

        for stat in response_data:
            type_institution = stat['type_institution']
            followers = stat['total_followers']
            if(stat['social_network'] == 'Facebook'):
                institution = TypeInstitution.objects.get(name=type_institution)
                percentage_correction = institution.percentage_correction_in_network_social
                print('tipo de institucion:', institution, 'percentage_correction', percentage_correction)
                print('followers sin el factor de correccion:', stat['total_followers'] )
                followers = followers - ( followers * percentage_correction / 100)
                # stat['total_followers'] = round(followers)
                print( '[end]','followers con el factor de correccion:', stat['total_followers'])
                followers_facebook += round(followers)
            elif (stat['social_network'] == 'X'):
                institution = TypeInstitution.objects.get(name=type_institution)
                percentage_correction = institution.percentage_correction_in_network_social
                print('tipo de institucion:', institution, 'percentage_correction', percentage_correction)
                print('followers sin el factor de correccion:', stat['total_followers'] )
                followers = followers - ( followers * percentage_correction / 100)
                # stat['total_followers'] = round(followers)
                print( '[end]','followers con el factor de correccion:', stat['total_followers'])
                followers_X += round(followers)
            if (stat['social_network'] == 'Instagram'):
                institution = TypeInstitution.objects.get(name=type_institution)
                percentage_correction = institution.percentage_correction_in_network_social
                print('tipo de institucion:', institution, 'percentage_correction', percentage_correction)
                print('followers sin el factor de correccion:', stat['total_followers'] )
                followers = followers - ( followers * percentage_correction / 100)
                # stat['total_followers'] = round(followers)
                print( '[end]','followers con el factor de correccion:', stat['total_followers'])
                followers_Instagram += round(followers)
            elif (stat['social_network'] == 'YouTube'):
                institution = TypeInstitution.objects.get(name=type_institution)
                percentage_correction = institution.percentage_correction_in_network_social
                print('tipo de institucion:', institution, 'percentage_correction', percentage_correction)
                print('followers sin el factor de correccion:', stat['total_followers'] )
                followers = followers - ( followers * percentage_correction / 100)
                # stat['total_followers'] = round(followers)
                print( '[end]','followers con el factor de correccion:', stat['total_followers'])
                followers_YouTube += round(followers)
            elif (stat['social_network'] == 'Tiktok'):
                institution = TypeInstitution.objects.get(name=type_institution)
                percentage_correction = institution.percentage_correction_in_network_social
                print('tipo de institucion:', institution, 'percentage_correction', percentage_correction)
                print('followers sin el factor de correccion:', stat['total_followers'] )
                followers = followers - ( followers * percentage_correction / 100)
                # stat['total_followers'] = round(followers)
                print( '[end]','followers con el factor de correccion:', stat['total_followers'])
                followers_Tiktok += round(followers)
            else:
                pass
        print('followers facebook', followers_facebook)
        print('followers X', followers_X )
        print('followers insta', followers_Instagram)
        print('followers youtube', followers_YouTube)
        print('followers tiktok', followers_Tiktok )

        return Response({
            "stats_date": stats_date,
            "unique_followers": {
                "facebook": followers_facebook,
                "X": followers_X,
                "Instagram": followers_Instagram,
                "YouTube": followers_YouTube,
                "Tiktok": followers_Tiktok
            },
            "stats": response_data,
        })

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_stats_by_category_id_and_date(request):
    try:
        type_institution_id = request.query_params.get('type_institution_id')
        stats_date = request.query_params.get('stats_date')

        # Validar que todos los parámetros necesarios estén presentes
        if not all([type_institution_id, stats_date]):
            return Response({
                "error": "type_institution_id y stats_date are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convertir la fecha de string a objeto date
        try:
            stats_date = datetime.strptime(stats_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "error": "Formato de fecha incorrecto. Use YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener la instancia de TypeInstitution
        type_institution = get_object_or_404(TypeInstitution, id=type_institution_id)

        # Obtener las estadísticas para la institución y fecha específicas
        stats = InstitutionStatsByType.objects.filter(
            type_institution=type_institution,
            stats_date=stats_date
        ).select_related('social_network')

        # Preparar la respuesta
        response_data = []
        for stat in stats:
            stat_data = {
                "type_institution": type_institution.name,
                "social_network": stat.social_network.name,
                "stats_date": stats_date.strftime("%Y-%m-%d"),
                "total_followers": stat.total_followers,
                "total_publications": stat.total_publications,
                "total_reactions": stat.total_reactions,
                "average_views": stat.average_views,
                "date_updated": stat.date_updated.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            }
            response_data.append(stat_data)

        #aplicar el factor de correccion al tipo de institucion
        for stat in response_data:
            followers = stat['total_followers']
            type_institution = stat['type_institution']
            
            p_correction = TypeInstitution.objects.get(name=type_institution)
            # se evalua adicional la red social de tiktok
            if (stat['social_network'] == 'Tiktok'):
                percentage = 5
                followers = followers - ( followers * percentage / 100)
                stat['total_followers'] = round(followers)
                print('seguidores en tiktok finales', stat['total_followers'] )
            else:
                percentage = p_correction.percentage_correction
                followers = followers - ( followers * percentage / 100)
                stat['total_followers'] = round(followers)
        print(response_data)

        return Response({
            "stats_date": stats_date,
            "stats": response_data
        })
        
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET','POST','PUT'])
def manage_stats(request):
    if request.method == 'GET':
        institution_type = request.GET.get('type_institution_id')
        if not institution_type:
            return get_stats_all_categories_by_date(request)
        else:
            return get_stats_by_category_id_and_date(request)
    elif request.method == 'POST':
        return create_institution_stats_api_t(request)
    
@api_view(['GET'])
def followers_uniques(request):
    all_stats = get_stats_all_categories_by_date(request)

    correction_factor_facebook = 100
    correction_factor_x = 75
    correction_factor_instagram = 50 
    correction_factor_tiktok = 80
    correction_factor_youtube = 50

    unique_followers = all_stats.data
    del unique_followers['stats']
    unique_followers['unique_followers']['facebook'] = round(unique_followers['unique_followers']['facebook'] * (correction_factor_facebook/100))
    unique_followers['unique_followers']['X'] = round(unique_followers['unique_followers']['X'] * (correction_factor_x/100))
    unique_followers['unique_followers']['Instagram'] = round(unique_followers['unique_followers']['Instagram'] * (correction_factor_instagram/100))
    unique_followers['unique_followers']['YouTube'] = round(unique_followers['unique_followers']['YouTube'] * (correction_factor_youtube/100))
    unique_followers['unique_followers']['Tiktok'] = round(unique_followers['unique_followers']['Tiktok'] * (correction_factor_tiktok/100))

    return Response({
        "data": unique_followers
    })
