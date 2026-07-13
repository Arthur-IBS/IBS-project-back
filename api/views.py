from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from .models import LogConfig
from .serializers import LogConfigSerializer
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import pytz
import os
import csv
import io
from dotenv import load_dotenv

load_dotenv()

IST = pytz.timezone('Asia/Kolkata')
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX_PREFIX = os.getenv("ES_INDEX_PREFIX", "logpro")

es = Elasticsearch([ES_HOST])


def get_latest_timestamp(index):
    """Get the latest @timestamp from ES index"""
    try:
        result = es.search(
            index=index,
            size=1,
            sort=[{"@timestamp": {"order": "desc"}}],
            query={"match_all": {}}
        )
        hits = result["hits"]["hits"]
        if hits:
            return hits[0]["_source"].get("@timestamp")
    except:
        pass
    return None


def build_query(levels, date_from, date_to, time_from, time_to, index=None):
    must = []

    if date_from and date_to:
        try:
            if time_from:
                start_str = datetime.strptime(
                    f"{date_from} {time_from}", "%Y-%m-%d %H:%M"
                ).strftime("%d.%m.%Y %H:%M:%S")
            else:
                start_str = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d.%m.%Y") + " 00:00:00"

            if time_to:
                end_str = datetime.strptime(
                    f"{date_to} {time_to}", "%Y-%m-%d %H:%M"
                ).strftime("%d.%m.%Y %H:%M:%S")
            else:
                end_str = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d.%m.%Y") + " 23:59:59"

            start_ist = IST.localize(datetime.strptime(start_str, "%d.%m.%Y %H:%M:%S"))
            end_ist = IST.localize(datetime.strptime(end_str, "%d.%m.%Y %H:%M:%S"))

            must.append({
                "range": {
                    "@timestamp": {
                        "gte": start_ist.isoformat(),
                        "lte": end_ist.isoformat()
                    }
                }
            })
        except ValueError:
            pass
    else:
        pass  # No date filter — return all logs sorted by @timestamp

    if levels:
        must.append({
            "terms": {"level.keyword": levels}
        })

    if not must:
        return {"match_all": {}}

    return {"bool": {"must": must}}


def format_hit(hit):
    src = hit["_source"]
    timestamp = src.get("log_timestamp", "")
    thread = src.get("thread", "")
    level = src.get("level", "")
    message = src.get("message", "")
    return f"[{timestamp}], {thread}, {level} {message}"


def get_index(app):
    if app == 'all':
        return f"{ES_INDEX_PREFIX}-*"
    return f"{ES_INDEX_PREFIX}-{app}"


@extend_schema(
    summary="Fetch log content",
    description="Returns paginated log lines from Elasticsearch with optional filters",
    parameters=[
        OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
        OpenApiParameter('app', OpenApiTypes.STR, description='Application name e.g. opsman. Use all for all apps'),
        OpenApiParameter('levels', OpenApiTypes.STR, description='Comma separated levels e.g. W,E'),
        OpenApiParameter('date_from', OpenApiTypes.DATE, description='Start date YYYY-MM-DD'),
        OpenApiParameter('date_to', OpenApiTypes.DATE, description='End date YYYY-MM-DD'),
        OpenApiParameter('time_from', OpenApiTypes.STR, description='Start time HH:MM requires date'),
        OpenApiParameter('time_to', OpenApiTypes.STR, description='End time HH:MM requires date'),
    ],
    responses={200: None}
)
@api_view(['GET'])
def get_log_content(request):
    app = request.GET.get('app', os.getenv("APP_NAME", "logs"))
    ES_INDEX = get_index(app)

    page = int(request.GET.get('page', 1))
    levels_param = request.GET.get('levels', None)
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    time_from = request.GET.get('time_from', None)
    time_to = request.GET.get('time_to', None)

    levels = [l.strip() for l in levels_param.split(',')] if levels_param else []

    if (time_from or time_to) and not (date_from and date_to):
        return Response(
            {'error': 'Please set a date range before filtering by time.'},
            status=400
        )

    page_size = 500
    offset = (page - 1) * page_size
    query = build_query(levels, date_from, date_to, time_from, time_to, index=ES_INDEX)

    try:
        result = es.search(
            index=ES_INDEX,
            query=query,
            size=page_size,
            from_=offset,
            sort=[{"@timestamp": {"order": "desc"}}],
            track_total_hits=True
        )
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]["value"]
    except Exception as e:
        return Response({'error': f'Elasticsearch error: {str(e)}'}, status=500)

    lines = [format_hit(h) for h in hits]
    lines = lines[::-1]

    has_more = (offset + page_size) < total

    window_start = ""
    window_end = ""
    latest_timestamp = ""
    if hits:
        window_end = hits[0]["_source"].get("log_timestamp", "")
        window_start = hits[-1]["_source"].get("log_timestamp", "")
        latest_timestamp = hits[0]["_source"].get("@timestamp", "")

    return Response({
        'lines': lines,
        'page': page,
        'total_lines': total,
        'has_more': has_more,
        'filename': f"{app}.log",
        'window_start': window_start,
        'window_end': window_end,
        'latest_timestamp': latest_timestamp,  # used by background refresh
    })


@extend_schema(
    summary="Fetch only new log lines since a given timestamp",
    description="Used by background auto-refresh. Returns only lines newer than the given since timestamp. React appends these to the bottom without touching scroll position.",
    parameters=[
        OpenApiParameter('since', OpenApiTypes.STR, required=True, description='ISO timestamp e.g. 2026-07-07T10:38:00+05:30'),
        OpenApiParameter('app', OpenApiTypes.STR, description='Application name'),
        OpenApiParameter('levels', OpenApiTypes.STR, description='Comma separated levels e.g. W,E'),
    ],
    responses={200: None}
)
@api_view(['GET'])
def get_latest_logs(request):
    """Returns only new log lines since a given @timestamp — for silent background refresh."""
    app = request.GET.get('app', os.getenv("APP_NAME", "logs"))
    ES_INDEX = get_index(app)

    since = request.GET.get('since', None)
    levels_param = request.GET.get('levels', None)
    levels = [l.strip() for l in levels_param.split(',')] if levels_param else []

    if not since:
        return Response({'error': 'since parameter is required'}, status=400)

    must = [
        {"range": {"@timestamp": {"gt": since}}}
    ]

    if levels:
        must.append({"terms": {"level.keyword": levels}})

    query = {"bool": {"must": must}}

    try:
        result = es.search(
            index=ES_INDEX,
            query=query,
            size=500,
            sort=[{"@timestamp": {"order": "asc"}}],  # asc so new lines go to bottom
            track_total_hits=True
        )
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]["value"]
    except Exception as e:
        return Response({'error': f'Elasticsearch error: {str(e)}'}, status=500)

    lines = [format_hit(h) for h in hits]

    latest_timestamp = ""
    if hits:
        latest_timestamp = hits[-1]["_source"].get("@timestamp", "")

    return Response({
        'lines': lines,
        'new_count': len(lines),
        'total_new': total,
        'latest_timestamp': latest_timestamp,
    })


@extend_schema(
    summary="Export logs as CSV",
    description="Downloads filtered logs as a CSV file",
    parameters=[
        OpenApiParameter('date_from', OpenApiTypes.DATE, required=True),
        OpenApiParameter('date_to', OpenApiTypes.DATE, required=True),
        OpenApiParameter('time_from', OpenApiTypes.STR),
        OpenApiParameter('time_to', OpenApiTypes.STR),
        OpenApiParameter('levels', OpenApiTypes.STR),
        OpenApiParameter('app', OpenApiTypes.STR),
    ],
    responses={200: None}
)
@api_view(['GET'])
def export_logs_csv(request):
    app = request.GET.get('app', os.getenv("APP_NAME", "logs"))
    ES_INDEX = get_index(app)

    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    time_from = request.GET.get('time_from', None)
    time_to = request.GET.get('time_to', None)
    levels_param = request.GET.get('levels', None)
    levels = [l.strip() for l in levels_param.split(',')] if levels_param else []

    if not date_from or not date_to:
        return Response({'error': 'date_from and date_to are required for export.'}, status=400)

    query = build_query(levels, date_from, date_to, time_from, time_to, index=ES_INDEX)

    try:
        result = es.search(
            index=ES_INDEX,
            query=query,
            size=10000,
            sort=[{"@timestamp": {"order": "asc"}}]
        )
        hits = result["hits"]["hits"]
    except Exception as e:
        return Response({'error': f'Elasticsearch error: {str(e)}'}, status=500)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['timestamp', 'thread', 'level', 'message'])

    for hit in hits:
        src = hit["_source"]
        writer.writerow([
            src.get("log_timestamp", ""),
            src.get("thread", ""),
            src.get("level", ""),
            src.get("message", ""),
        ])

    output.seek(0)
    filename = f"logs_{app}_{date_from}_to_{date_to}.csv"
    response = HttpResponse(output, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@extend_schema(
    summary="Get all configured applications",
    description="Returns list of all applications configured in LogConfig table",
    responses={200: None}
)
@api_view(['GET'])
def get_apps(request):
    configs = LogConfig.objects.all()
    app_list = []
    for c in configs:
        app_list.append({
            "app_name": c.app_name,
            "es_index": c.es_index,
            "location": c.location,
            "log_format": c.log_format,
        })
    return Response(app_list)


@extend_schema(
    summary="Set, update, or list log app configs",
    description="GET lists all configured apps. POST/PUT adds or updates an app's config.",
    responses={200: LogConfigSerializer}
)
@api_view(['GET', 'POST', 'PUT'])
def manage_log_location(request):
    if request.method == 'GET':
        configs = LogConfig.objects.all()
        serializer = LogConfigSerializer(configs, many=True)
        return Response(serializer.data)

    app_name = request.data.get('app_name')
    location = request.data.get('location')
    log_format = request.data.get('log_format', 'opsman')

    if not app_name or not location:
        return Response({'error': 'app_name and location are required'}, status=400)

    es_index = request.data.get('es_index', f"{ES_INDEX_PREFIX}-{app_name}")

    config, created = LogConfig.objects.update_or_create(
        app_name=app_name,
        defaults={
            'location': location,
            'log_format': log_format,
            'es_index': es_index,
        }
    )

    serializer = LogConfigSerializer(config)

    if created:
        return Response(serializer.data, status=201)
    else:
        return Response(serializer.data, status=200)
