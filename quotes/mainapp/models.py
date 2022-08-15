from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class CustomUser(AbstractUser):
    pass


class Quote(models.Model):
    code = models.CharField(max_length=127)
    name = models.CharField(max_length=127)
    price = models.FloatField()
    date = models.DateTimeField()
    denomination = models.IntegerField()
