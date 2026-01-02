from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from .models import TeamMember
from .service import get_or_create_dynamic_id


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
            telegram_id=validated_data.get('telegram_id', '')
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
            role=TeamMember.Roles.MEMBER,
            is_accepted=False
        )

    def validate(self, attrs):
        code = attrs.get('dynamic_id')
        team = self.context.get("team")
        request_user = self.context.get("request").user

        invitee = get_user_id_by_dynamic_code(code)

        if not invitee:
            raise serializers.ValidationError({"dynamic_id": "Код недействителен или устарел."})

        try:
            invitee = User.objects.get(id=invitee)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"dynamic_id": "Пользователь, владеющий этим кодом, больше не существует."}
            )

        if invitee == request_user:
            raise serializers.ValidationError("Вы не можете пригласить самого себя.")

        if TeamMember.objects.filter(user=invitee, team=team).exists():
            raise serializers.ValidationError("Пользователь уже является участником или приглашен.")

        attrs['invitee_user_object'] = invitee
        return attrs