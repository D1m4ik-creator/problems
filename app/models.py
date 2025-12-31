from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(max_length=100, blank=True, null= True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    telegram_id = models.CharField(max_length=32, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username