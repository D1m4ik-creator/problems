from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app.views import RegistrationAPIView, LoginAPIView, LogoutAPIView, MeView, TeamViewSet


router = DefaultRouter()
router.register(r"teams", TeamViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    # Работа с командой
    path("api/", include(router.urls)),
    # Токены для авторизации SimpleJWT и кастомной регистрации
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("api/register/", RegistrationAPIView.as_view(), name="register"), # Регистрация
    path("api/login/", LoginAPIView.as_view(), name="login"),# Вход
    path("api/logout/", LogoutAPIView.as_view(), name="logout"), # Выход

    # Возвращаем данные текущего пользователя
    path("api/auth/me/", MeView.as_view(), name="me"),

    # Документация
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
