from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
import hashlib
import time
import string
import random

def generate_unique_id():
    # Генерирует код типа TASK-73A9 (8 символов)
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=8))

#Пользователи
class User(AbstractUser):
    username = models.CharField(max_length=100, blank=True, null= True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    telegram_id = models.CharField(max_length=32, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)
    secret_key = models.CharField(max_length=50, default=generate_unique_id)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def dynamic_id(self):
        current_minute = int(time.time() // 60)
        raw_string = f"{self.secret_key}-{current_minute}"
        # Генерируем хеш
        hash_digest = hashlib.sha256(raw_string.encode()).hexdigest()
        return f"TASK-{hash_digest[:8].upper()}"

    def __str__(self):
        return self.username


#Команды
class Team(models.Model):
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_teams")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="TeamMember", related_name="teams")
    created_at = models.DateTimeField(auto_now_add=True)


# Выбор роли в команде
class TeamMember(models.Model):
    class Roler(models.TextChoices):
        ADMIN = "admin", "Администратор"
        MEMBER = "member", "Участник"
        VIEWER = "viewer", "наблюдатель"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=15, choices=Roler.choices, default=Roler.MEMBER)

    # Приглашение
    is_accepted = models.BooleanField(default=False)
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'team')

#Проекты
class Projects(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.name