from rest_framework import serializers
from .models import LogConfig, LogEntry
 
class LogConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogConfig
        fields = '__all__'
 
class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'
 