from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LeaveTypeViewSet, LeavePolicyViewSet, LeaveBalanceViewSet, 
    LeaveRequestViewSet, LeaveCommentViewSet, HolidayViewSet
)

router = DefaultRouter()
router.register(r'leaveType', LeaveTypeViewSet)
router.register(r'leavePolicy', LeavePolicyViewSet)
router.register(r'leaveBalance', LeaveBalanceViewSet)
router.register(r'leaveRequest', LeaveRequestViewSet)
router.register(r'leaveCommen', LeaveCommentViewSet)
router.register(r'Holiday', HolidayViewSet)


urlpatterns = [
    path('', include(router.urls)),
]