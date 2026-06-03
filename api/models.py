from django.db import models
 
class LogConfig(models.Model):
    location = models.CharField(max_length=500)
 
    class Meta:
        db_table = 'log_config'
 
 
class LogEntry(models.Model):
    timestamp = models.DateTimeField()
    level = models.CharField(max_length=1)
    thread = models.CharField(max_length=50)
    message = models.TextField()
 
    class Meta:
        db_table = 'log_entry'
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['level', 'timestamp']),
        ]
 