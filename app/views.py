from django.contrib.auth import authenticate
from django.db import models
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import *
from .service import get_or_create_dynamic_id
from .models import Team, TeamMember, Projects, Task


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Возвращаем данные текущего пользователя")
    def get(self, request):
        dynamic_id = get_or_create_dynamic_id(request.user)

        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "public_id": dynamic_id
        })


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация нового пользователя",
        description="Принимает данные пользователя, создает аккаунт и возвращает JWT токены.",
        request=UserRegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Успешная регистрация",
                response=UserSerializer  # Можно указать схему ответа
            ),
            400: OpenApiResponse(description="Ошибка валидации данных")
        },
        tags=["Аутентификация"]  # Группирует эндпоинты в интерфейсе
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return Response({
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Авторизация пользователя",
        description="Принимает данные пользователя и возвращает JWT токены.",
        request=UserSerializer,
        responses={
            201: OpenApiResponse(
                description="Успешная аутентификация",
            ),
            400: OpenApiResponse(description="Ошибка валидации данных")
        },
        tags=["Аутентификация"]  # Группирует эндпоинты в интерфейсе
    )
    def post(self, request):
        data = request.data
        email = data.get("email", None)
        username = data.get('username', None)
        password = data.get('password', None)
        if email is None or password is None:
            return Response({'error': 'Нужен и логин, и пароль'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, email=email, password=password)
        print(user)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)

        return Response({"detail": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Выход из системы (отзыв токена)",
        description="Принимает refresh токен и заносит его в черный список. После этого токен станет недействительным.",
        request=LogoutSerializer,
        responses={
            205: OpenApiResponse(description="Успешный выход, токен отозван"),
            400: OpenApiResponse(description="Неверный или просроченный токен"),
            401: OpenApiResponse(description="Пользователь не авторизован")
        },
        tags=["Аутентификация"]
    )

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Необходим Refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist() # Добавляем в чёрный список

        except TokenError:
            return Response({'error': 'Неверный Refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': 'Выход успешен'}, status=status.HTTP_200_OK)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializers

    def get_queryset(self):
        user = self.request.user
        return Team.objects.filter(
        models.Q(owner=user) | models.Q(teammember__user=user)
    ).distinct()

    def perform_create(self, serializer):
        team = serializer.save(owner=self.request.user)

        TeamMember.objects.create(
            team=team,
            user=self.request.user,
            role="owner"
        )

    @extend_schema(request=TeamMemberCreateSerializer, responses={201: None})
    @action(detail=True, methods=["post"], url_path='invite-by-dynamic-id')
    def invite_by_dynamic_id(self, request, pk=None):
        team = self.get_object()

        serializer = TeamMemberCreateSerializer(
            data=request.data,
            context={'team': team, 'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Приглашение успешно отправлено"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=TeamMemberSerializer, responses={201: None})
    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        team = self.get_object()
        members = TeamMember.objects.filter(team=team).select_related()
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)

    @extend_schema(request=ProjectsSerializers, responses={201: None})
    @action(detail=True, methods=["get", "post"], url_path="projects")
    def projects(self, requests, pk=None):
        team = self.get_object()

        if requests.method == "GET":
            projects = team.projects.all().order_by("-created_at")
            serializer = ProjectsSerializers(projects, many=True)
            return Response(serializer.data)

        if requests.method == "POST":
            serializer = ProjectsSerializers(data=requests.data)
            if serializer.is_valid():
                serializer.save(team=team)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        project_id = self.request.query_params.get("project_id")

        queryset = Task.objects.filter(project__team__members=user).distinct()
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.order_by("priority", "-created_at")

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"], url_path="send-to-review")
    def send_to_review(self, request, pk=None):
        task = self.get_object()

        try:
            task.send_to_review()
            return Response({'detail': 'Задача отправлена на проверку', 'status': task.status})

        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="move")
    def move_task(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get("status")

        if new_status in Task.Status.values:
            task.status = new_status
            task.save(update_fields=["status", "created_at"])
            return Response({'status': task.status})

        return Response({'detail': 'Недопустимый статус'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectsViewSet(viewsets.ModelViewSet):
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Projects.objects.filter(team__members=self.request.user).distinct()
