from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, DesignationViewSet, EmployeeViewSet, 
    EmployeeEducationViewSet, 
    EmployeeExperienceViewSet, EmployeeSkillViewSet, 
    EmployeeTimelineViewSet
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'designations', DesignationViewSet)
router.register(r'employees', EmployeeViewSet)
# router.register(r'documents', EmployeeDocumentViewSet)
router.register(r'education', EmployeeEducationViewSet)
router.register(r'experience', EmployeeExperienceViewSet)
router.register(r'skills', EmployeeSkillViewSet)
router.register(r'timeline', EmployeeTimelineViewSet)

urlpatterns = [
    path('', include(router.urls)),
]