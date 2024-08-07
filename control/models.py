from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class Robot(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

