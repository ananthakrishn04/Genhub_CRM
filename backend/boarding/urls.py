from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProcessTemplateViewSet,
    TaskTemplateViewSet,
    ProcessViewSet,
    TaskViewSet,
    EquipmentViewSet,
    EquipmentAssignmentViewSet
)

router = DefaultRouter()
router.register(r'process-templates', ProcessTemplateViewSet)
router.register(r'task-templates', TaskTemplateViewSet)
router.register(r'processes', ProcessViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'equipment-assignments', EquipmentAssignmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]