from .models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username", "email", "telegram_id"]
        read_only_fields = ["id"]


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