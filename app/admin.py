from django.contrib import admin
from .models import Team, TeamMember,User, Projects


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    fields = ('user', 'role', 'is_accepted', 'invited_at')
    readonly_fields = ('invited_at',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'member_count', 'created_at')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('created_at',)
    inlines = [TeamMemberInline]

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = "Членов в команде"


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'get_status', 'invited_at')
    list_filter = ('is_accepted', 'role', 'team')
    search_fields = ('user__username', 'team__name')
    readonly_fields = ('invited_at',)

    def get_status(self, obj):
        return "✓ Принято" if obj.is_accepted else "⏳ Ожидание"
    get_status.short_description = "Статус приглашения"

admin.site.register(User)
admin.site.register(Projects)