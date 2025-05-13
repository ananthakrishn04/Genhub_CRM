from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentCategoryViewSet,
    TemplateViewSet,
    DocumentViewSet,
    DocumentVersionViewSet,
    DocumentSignatureViewSet
)

router = DefaultRouter()
router.register(r'categories', DocumentCategoryViewSet)
router.register(r'templates', TemplateViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'versions', DocumentVersionViewSet)
router.register(r'signatures', DocumentSignatureViewSet)

urlpatterns = [
    path('', include(router.urls)),
]