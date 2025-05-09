from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import LeaveType, LeavePolicy, LeaveBalance, LeaveRequest, LeaveComment, Holiday
from .serializers import (
    LeaveTypeSerializer, LeavePolicySerializer, LeaveBalanceSerializer,
    LeaveRequestListSerializer, LeaveRequestDetailSerializer, 
    LeaveRequestCreateSerializer, LeaveRequestUpdateSerializer,
    LeaveCommentSerializer, HolidaySerializer
)
from employees.models import Employee

class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_paid', 'requires_approval']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class LeavePolicyViewSet(viewsets.ModelViewSet):
    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['leave_type', 'department', 'designation', 'carries_forward']
    search_fields = ['leave_type__name']
    ordering_fields = ['leave_type__name', 'days_allowed', 'created_at']

class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'leave_type', 'year']
    search_fields = ['employee__first_name', 'employee__last_name', 'leave_type__name']
    ordering_fields = ['employee__first_name', 'leave_type__name', 'year']

    @action(detail=False, methods=['get'])
    def employee_balances(self, request):
        employee_id = request.query_params.get('employee_id')
        year = request.query_params.get('year', datetime.now().year)
        
        if not employee_id:
            return Response({"error": "Employee ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        
        balances = LeaveBalance.objects.filter(employee=employee, year=year)
        serializer = self.get_serializer(balances, many=True)
        return Response(serializer.data)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'leave_type', 'status', 'start_date', 'end_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'status']

    def get_serializer_class(self):
        if self.action == 'list':
            return LeaveRequestListSerializer
        elif self.action == 'create':
            return LeaveRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LeaveRequestUpdateSerializer
        return LeaveRequestDetailSerializer

    @action(detail=False, methods=['get'])
    def my_leaves(self, request):
        employee_id = request.query_params.get('employee_id')
        
        if not employee_id:
            return Response({"error": "Employee ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        
        leave_requests = LeaveRequest.objects.filter(employee=employee)
        
        # Filter by status if provided
        status_param = request.query_params.get('status')
        if status_param:
            leave_requests = leave_requests.filter(status=status_param)
            
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            leave_requests = leave_requests.filter(
                Q(start_date__gte=start_date, start_date__lte=end_date) |
                Q(end_date__gte=start_date, end_date__lte=end_date)
            )
        
        serializer = LeaveRequestListSerializer(leave_requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        manager_id = request.query_params.get('manager_id')
        
        if not manager_id:
            return Response({"error": "Manager ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            manager = Employee.objects.get(id=manager_id)
        except Employee.DoesNotExist:
            return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all employees reporting to this manager
        team_members = Employee.objects.filter(reporting_manager=manager)
        
        # Get all pending leave requests from team members
        leave_requests = LeaveRequest.objects.filter(
            employee__in=team_members, 
            status='PENDING'
        )
        
        serializer = LeaveRequestListSerializer(leave_requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def team_calendar(self, request):
        manager_id = request.query_params.get('manager_id')
        start_date = request.query_params.get('start_date', timezone.now().date().replace(day=1).isoformat())
        end_date = request.query_params.get('end_date', (timezone.now().date().replace(day=1) + timedelta(days=31)).replace(day=1).isoformat())
        
        if not manager_id:
            return Response({"error": "Manager ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            manager = Employee.objects.get(id=manager_id)
        except Employee.DoesNotExist:
            return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all employees reporting to this manager, including the manager
        team_members = list(Employee.objects.filter(reporting_manager=manager))
        team_members.append(manager)  # Include the manager
        
        # Get all approved leave requests from team members in the date range
        leave_requests = LeaveRequest.objects.filter(
            employee__in=team_members,
            status='APPROVED',
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        serializer = LeaveRequestListSerializer(leave_requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        leave_request = self.get_object()
        
        employee_id = request.data.get('employee')
        comment = request.data.get('comment')
        
        if not employee_id or not comment:
            return Response({"error": "Employee ID and comment are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        
        leave_comment = LeaveComment.objects.create(
            leave_request=leave_request,
            employee=employee,
            comment=comment
        )
        
        serializer = LeaveCommentSerializer(leave_comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LeaveCommentViewSet(viewsets.ModelViewSet):
    queryset = LeaveComment.objects.all()
    serializer_class = LeaveCommentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['leave_request', 'employee']

class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_recurring', 'applicable_departments']
    search_fields = ['name', 'description']
    ordering_fields = ['date', 'name']

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        today = timezone.now().date()
        end_date = today + timedelta(days=90)  # Next 90 days
        
        holidays = Holiday.objects.filter(
            date__gte=today,
            date__lte=end_date
        )
        
        # Also include recurring holidays that might fall in this range
        current_year = today.year
        recurring_holidays = Holiday.objects.filter(is_recurring=True)
        
        for holiday in recurring_holidays:
            # Create a date for this year's occurrence
            this_year_date = holiday.date.replace(year=current_year)
            
            # If it falls in our range and isn't already included, add it
            if today <= this_year_date <= end_date and not holidays.filter(date=this_year_date, name=holiday.name).exists():
                holidays |= Holiday.objects.filter(pk=holiday.pk)
        
        serializer = self.get_serializer(holidays, many=True)
        return Response(serializer.data)