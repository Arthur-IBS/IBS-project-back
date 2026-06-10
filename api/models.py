from django.db import models
 
class LogConfig(models.Model):
    location = models.CharField(max_length=500)
 
    class Meta:
        db_table = 'log_config'