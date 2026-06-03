from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import Http404, HttpResponse
from .models import LogConfig, LogEntry
from .serializers import LogConfigSerializer
from datetime import datetime, timedelta
import pytz
import os
import csv
import io
 
IST = pytz.timezone('Asia/Kolkata')
 
 
def parse_new_line(line):
    try:
        line = line.strip()
        if not line.startswith('['):
            return None
        dt_str = line[1:20]
        timestamp = datetime.strptime(dt_str, "%d.%m.%Y %H:%M:%S")
        timestamp = IST.localize(timestamp)
        parts = line.split(', ', 2)
        if len(parts) < 3:
            return None
        thread = parts[1].strip()
        remainder = parts[2].strip()
        if not remainder:
            return None
        level = remainder[0]
        message = remainder[1:].strip()
        return {
            'timestamp': timestamp,
            'level': level,
            'thread': thread,
            'message': message,
        }
    except:
        return None
 
 
def sync_new_logs(file_path):
    last_entry = LogEntry.objects.order_by('-timestamp').first()
    last_timestamp = last_entry.timestamp if last_entry else None
 
    batch = []
    current_line = ''
 
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            stripped = line.strip()
 
            if not stripped:
                continue
 
            if stripped.startswith('['):
                if current_line:
                    parsed = parse_new_line(current_line)
                    if parsed:
                        if last_timestamp is None or parsed['timestamp'] > last_timestamp:
                            batch.append(LogEntry(**parsed))
                        if len(batch) >= 1000:
                            LogEntry.objects.bulk_create(batch, ignore_conflicts=True)
                            batch = []
                current_line = stripped
            else:
                current_line += ' ' + stripped
 
        if current_line:
            parsed = parse_new_line(current_line)
            if parsed:
                if last_timestamp is None or parsed['timestamp'] > last_timestamp:
                    batch.append(LogEntry(**parsed))
 
    if batch:
        LogEntry.objects.bulk_create(batch, ignore_conflicts=True)
 
 
@api_view(['GET'])
def get_log_content(request):
    try:
        config = LogConfig.objects.get(id=1)
    except LogConfig.DoesNotExist:
        return Response({'error': 'Log location not configured yet.'}, status=404)
 
    file_path = config.location
 
    if not os.path.exists(file_path):
        raise Http404("Log file not found")
 
    try:
        sync_new_logs(file_path)
    except Exception:
        pass
 
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
 
    queryset = LogEntry.objects.all()
 
    if date_from and date_to:
        try:
            start_dt = IST.localize(datetime.strptime(date_from, "%Y-%m-%d").replace(hour=0, minute=0, second=0))
            end_dt = IST.localize(datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
            queryset = queryset.filter(timestamp__range=(start_dt, end_dt))
        except ValueError:
            return Response({'error': 'Invalid date format.'}, status=400)
    else:
        # default — last 1 hour from latest entry
        latest = LogEntry.objects.order_by('-timestamp').first()
        if latest:
            one_hour_ago = latest.timestamp - timedelta(hours=1)
            queryset = queryset.filter(timestamp__gte=one_hour_ago)
 
    # time of day filter
    if time_from or time_to:
        time_from_dt = datetime.strptime(time_from, "%H:%M") if time_from else None
        time_to_dt = datetime.strptime(time_to, "%H:%M") if time_to else None
        filtered_ids = []
        for entry in queryset:
            ist_time = entry.timestamp.astimezone(IST)
            entry_minutes = ist_time.hour * 60 + ist_time.minute
            if time_from_dt:
                if entry_minutes < time_from_dt.hour * 60 + time_from_dt.minute:
                    continue
            if time_to_dt:
                if entry_minutes > time_to_dt.hour * 60 + time_to_dt.minute:
                    continue
            filtered_ids.append(entry.id)
        queryset = LogEntry.objects.filter(id__in=filtered_ids)
 
    if levels:
        queryset = queryset.filter(level__in=levels)
 
    page_size = 500
    total = queryset.count()
    queryset = queryset.order_by('-timestamp')
    offset = (page - 1) * page_size
    entries = list(queryset[offset:offset + page_size])
    has_more = (offset + page_size) < total
 
    lines = []
    for entry in entries:
        dt = entry.timestamp.astimezone(IST).strftime("%d.%m.%Y %H:%M:%S")
        line = f"[{dt}], {entry.thread}, {entry.level}  {entry.message}"
        lines.append(line)
 
    if entries:
        window_start = entries[-1].timestamp.astimezone(IST).strftime("%d.%m.%Y %H:%M:%S")
        window_end = entries[0].timestamp.astimezone(IST).strftime("%d.%m.%Y %H:%M:%S")
    else:
        window_start = window_end = ""
 
    return Response({
        'lines': lines,
        'page': page,
        'total_lines': total,
        'has_more': has_more,
        'filename': os.path.basename(file_path),
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
 
    try:
        start_dt = IST.localize(datetime.strptime(date_from, "%Y-%m-%d").replace(hour=0, minute=0, second=0))
        end_dt = IST.localize(datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
    except ValueError:
        return Response({'error': 'Invalid date format.'}, status=400)
 
    queryset = LogEntry.objects.filter(timestamp__range=(start_dt, end_dt))
 
    if levels:
        queryset = queryset.filter(level__in=levels)
 
    if time_from or time_to:
        time_from_dt = datetime.strptime(time_from, "%H:%M") if time_from else None
        time_to_dt = datetime.strptime(time_to, "%H:%M") if time_to else None
        filtered_ids = []
        for entry in queryset:
            ist_time = entry.timestamp.astimezone(IST)
            entry_minutes = ist_time.hour * 60 + ist_time.minute
            if time_from_dt:
                if entry_minutes < time_from_dt.hour * 60 + time_from_dt.minute:
                    continue
            if time_to_dt:
                if entry_minutes > time_to_dt.hour * 60 + time_to_dt.minute:
                    continue
            filtered_ids.append(entry.id)
        queryset = LogEntry.objects.filter(id__in=filtered_ids)
 
    queryset = queryset.order_by('timestamp')
 
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['timestamp', 'thread', 'level', 'message'])
 
    for entry in queryset:
        writer.writerow([
            entry.timestamp.astimezone(IST).strftime("%d.%m.%Y %H:%M:%S"),
            entry.thread,
            entry.level,
            entry.message,
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
 