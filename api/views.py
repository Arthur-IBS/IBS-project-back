from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import FileResponse, Http404
from .models import LogConfig
from .serializers import LogConfigSerializer
import os
 
# GET - fetch log file content from location stored in db
@api_view(['GET'])
def get_log_content(request):
    try:
        config = LogConfig.objects.get(id=1)
    except LogConfig.DoesNotExist:
        return Response({'error': 'Log location not configured yet. Do a POST first.'}, status=404)
 
    file_path = config.location
 
    if not os.path.exists(file_path):
        raise Http404("Log file not found at configured location")
 
    with open(file_path, 'r') as f:
        content = f.read()
 
    return Response({
        'filename': os.path.basename(file_path),
        'content': content
    })
 
 
# POST - save log file location to db for the first time
@api_view(['POST'])
def set_log_location(request):
    serializer = LogConfigSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
 
 
# PUT - update existing log file location
@api_view(['PUT'])
def update_log_location(request, pk):
    try:
        config = LogConfig.objects.get(pk=pk)
    except LogConfig.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)
 
    serializer = LogConfigSerializer(config, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)
 