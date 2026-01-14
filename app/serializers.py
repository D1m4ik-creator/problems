from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from .models import TeamMember, Team, Projects, Task
from .service import get_or_create_dynamic_id, get_user_id_by_dynamic_code


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "telegram_id"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "telegram_id": {"required": False, "allow_blank": True, "allow_null": True},
            "username": {"required": False, "allow_blank": True, "allow_null": True},
        }

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'telegram_id']
        extra_kwargs = {
            "telegram_id": {"required": False, "allow_blank": True, "allow_null": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
        )

        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Refresh токен, который нужно отозвать")


class TeamMemberCreateSerializer(serializers.Serializer):
    dynamic_id = serializers.CharField(write_only=True)

    def create(self, validated_data):
        team = self.context.get('team')
        invitee = validated_data.get('invitee')

        return TeamMember.objects.create(
            user=invitee,
            team=team,
            role=TeamMember.Roler.MEMBER,
            is_accepted=False
        )

    def validate(self, attrs):
        code = attrs.get('dynamic_id')
        team = self.context.get("team")
        request_user = self.context.get("request").user
        invitee_id = get_user_id_by_dynamic_code(code)
        if not invitee_id:
            raise serializers.ValidationError({"dynamic_id": "Код недействителен или устарел."})

        try:
            invitee = User.objects.get(id=invitee_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"dynamic_id": "Пользователь, владеющий этим кодом, больше не существует."}
            )

        if invitee == request_user:
            raise serializers.ValidationError("Вы не можете пригласить самого себя.")

        if TeamMember.objects.filter(user=invitee, team=team).exists():
            raise serializers.ValidationError("Пользователь уже является участником или приглашен.")

        attrs['invitee'] = invitee
        return attrs


class UserSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', "email"]


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "user", "role", "role_display", "is_accepted"]


class TeamSerializers(serializers.ModelSerializer):
    owner = UserSimpleSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "name", "owner", "created_at", "member_count"]

    def get_member_count(self, obj):
        return obj.members.count()


class ProjectsSerializers(serializers.ModelSerializer):
    task_count = serializers.IntegerField(source="task.count", read_only=True)

    class Meta:
        model = Projects
        fields = ["id", "name", "description", "created_at", "team", "task_count"]
        read_only_fields = ["team"]


class TaskSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title","description", "status_display", "priority_display", "status", "priority", "assigned_to", "assigned_to_username", "project", "created_at"]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_priority_display(self, obj):
        return obj.get_priority_display()

