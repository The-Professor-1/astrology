from django.db import models # type: ignore

# Create your models here.
class Users(models.Model):
    selfname = models.CharField(max_length=100)
    mothersname = models.CharField(max_length=100)
    sign = models.CharField(max_length=100)
    description = models.CharField(default='',max_length=10000)
class Message_After_Transaction(models.Model):
    username = models.CharField(max_length=100)
    transaction_number = models.CharField(max_length=100)
    status = models.CharField(max_length=100,default='denied')
class Allowed_Users(models.Model):
    username = models.CharField(max_length=100)
    status = models.CharField(max_length=100)