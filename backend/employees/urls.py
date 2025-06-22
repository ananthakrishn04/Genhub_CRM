from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'designations', views.DesignationViewSet)
router.register(r'employees', views.EmployeeViewSet)
# router.register(r'documents', EmployeeDocumentViewSet)
router.register(r'education', views.EmployeeEducationViewSet)
router.register(r'experience', views.EmployeeExperienceViewSet)
router.register(r'skills', views.EmployeeSkillViewSet)
router.register(r'timeline', views.EmployeeTimelineViewSet)
router.register(r'attendance', views.EmployeeAttendanceViewSet, basename='attendance')
router.register(r'task-time-logs', views.TaskTimeLogViewSet, basename='task-time-logs')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.LoginView.as_view(), name='employee-login'),
]