from django.db import models

# Create your models here.

class Entries(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return self.result
