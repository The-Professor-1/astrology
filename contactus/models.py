from django.db import models # type: ignore

# Create your models here.
class Message(models.Model):
    name = models.CharField(max_length=40)
    email = models.EmailField(max_length=100)
    message = models.TextField(max_length=500)