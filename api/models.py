from django.db import models
 
 
class LogConfig(models.Model):
    app_name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=500)
    log_format = models.CharField(max_length=50)
    es_index = models.CharField(max_length=100)
 
    class Meta:
        db_table = 'log_config'
 
    def __str__(self):
        return self.app_name
 