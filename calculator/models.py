from django.db import models # type: ignore

# Create your models here.
class Users(models.Model):
    selfname = models.CharField(max_length=100)
    mothersname = models.CharField(max_length=100)
    sign = models.CharField(max_length=100)
    description = models.CharField(default='',max_length=10000)
