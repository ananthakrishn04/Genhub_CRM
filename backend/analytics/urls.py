from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ReportExecutionViewSet, CertificateViewSet, HRMetricViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet)
router.register(r'report-executions', ReportExecutionViewSet)
router.register(r'certificates', CertificateViewSet)
router.register(r'hr-metrics', HRMetricViewSet)

app_name = 'analytics'

urlpatterns = [
    path('api/', include(router.urls)),
]