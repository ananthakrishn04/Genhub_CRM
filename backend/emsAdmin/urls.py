from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserPermissionViewSet,
    AdminLoginView
)

router = DefaultRouter()
router.register(r'user-permissions', UserPermissionViewSet, basename='user-permissions')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', AdminLoginView.as_view(), name='admin-login'),
]