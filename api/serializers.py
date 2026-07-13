from rest_framework import serializers
from .models import LogConfig
 
 
class LogConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogConfig
        fields = '__all__'
 