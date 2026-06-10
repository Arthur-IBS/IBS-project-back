from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from .models import LogConfig
from .serializers import LogConfigSerializer
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import pytz
import os
import csv
import io
 
IST = pytz.timezone('Asia/Kolkata')
ES_HOST = "http://localhost:9200"
ES_INDEX = "logpro-logs"
 
es = Elasticsearch([ES_HOST])
 
 
def build_query(levels, date_from, date_to, time_from, time_to):
    must = []
 
    # Date + time range filter using log_timestamp string field
    if date_from and date_to:
        try:
            # Build start and end as full datetime strings matching log_timestamp format
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
 
            # Use @timestamp for range but convert IST to UTC
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
 
    # Level filter
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
 
 
@api_view(['GET'])
def get_log_content(request):
    try:
        config = LogConfig.objects.get(id=1)
    except LogConfig.DoesNotExist:
        return Response({'error': 'Log location not configured yet.'}, status=404)
 
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
    query = build_query(levels, date_from, date_to, time_from, time_to)
 
    try:
        result = es.search(
            index=ES_INDEX,
            query=query,
            size=page_size,
            from_=offset,
            sort=[{"@timestamp": {"order": "desc"}}]
        )
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]["value"]
    except Exception as e:
        return Response({'error': f'Elasticsearch error: {str(e)}'}, status=500)
 
    lines = [format_hit(h) for h in hits]
 
    # Reverse so oldest at top, latest at bottom — CMD/terminal style
    lines = lines[::-1]
 
    has_more = (offset + page_size) < total
 
    window_start = ""
    window_end = ""
    if hits:
        window_end = hits[0]["_source"].get("log_timestamp", "")
        window_start = hits[-1]["_source"].get("log_timestamp", "")
 
    return Response({
        'lines': lines,
        'page': page,
        'total_lines': total,
        'has_more': has_more,
        'filename': os.path.basename(config.location),
        'window_start': window_start,
        'window_end': window_end,
    })
 
 
@api_view(['GET'])
def export_logs_csv(request):
    try:
        config = LogConfig.objects.get(id=1)
    except LogConfig.DoesNotExist:
        return Response({'error': 'Log location not configured yet.'}, status=404)
 
    date_from = request.GET.get('date_from', None)
    date_to = request.GET.get('date_to', None)
    time_from = request.GET.get('time_from', None)
    time_to = request.GET.get('time_to', None)
    levels_param = request.GET.get('levels', None)
    levels = [l.strip() for l in levels_param.split(',')] if levels_param else []
 
    if not date_from or not date_to:
        return Response({'error': 'date_from and date_to are required for export.'}, status=400)
 
    query = build_query(levels, date_from, date_to, time_from, time_to)
 
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
    filename = f"logs_{date_from}_to_{date_to}.csv"
    response = HttpResponse(output, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
 
 
@api_view(['POST', 'PUT'])
def manage_log_location(request):
    location = request.data.get('location')
 
    if not location:
        return Response({'error': 'location is required'}, status=400)
 
    config, created = LogConfig.objects.update_or_create(
        id=1,
        defaults={'location': location}
    )
 
    serializer = LogConfigSerializer(config)
 
    if created:
        return Response(serializer.data, status=201)
    else:
        return Response(serializer.data, status=200)
 