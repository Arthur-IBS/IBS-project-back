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