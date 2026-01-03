from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Team, TeamMember, Projects
User = get_user_model()

admin.site.register(User)
admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(Projects)