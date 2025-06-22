from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .filters import EmployeeFilter

from .models import (
    Department, Designation, Employee,EmployeeEducation, 
    EmployeeExperience, EmployeeSkill, EmployeeTimeline,
    EmployeeAttendance, TaskTimeLog
)

from boarding.models import Task

from .serializers import (
    DepartmentSerializer, DesignationSerializer, EmployeeListSerializer,
    EmployeeDetailSerializer, EmployeeCreateUpdateSerializer,
    EmployeeEducationSerializer, EmployeeExperienceSerializer, EmployeeSkillSerializer,
    EmployeeTimelineSerializer, EmployeeAttendanceSerializer, TaskSerializer, TaskTimeLogSerializer,
    UserLoginSerializer
)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent_department']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        department = self.get_object()
        employees = Employee.objects.filter(department=department)
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)

class DesignationViewSet(viewsets.ModelViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'department']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'department__name', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ['first_name', 'last_name', 'email', 'employee_id', 'skills']
    ordering_fields = ['first_name', 'last_name', 'date_of_joining', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeDetailSerializer

    # @action(detail=True, methods=['get'])
    # def documents(self, request, pk=None):
    #     employee = self.get_object()
    #     documents = employee.documents.all()
    #     serializer = EmployeeDocumentSerializer(documents, many=True)
    #     return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def education(self, request, pk=None):
        employee = self.get_object()
        education = employee.education.all()
        serializer = EmployeeEducationSerializer(education, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def experiences(self, request, pk=None):
        employee = self.get_object()
        experiences = employee.experiences.all()
        serializer = EmployeeExperienceSerializer(experiences, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def skills(self, request, pk=None):
        employee = self.get_object()
        skills = employee.skill_list.all()
        serializer = EmployeeSkillSerializer(skills, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        employee = self.get_object()
        timeline = employee.timeline.all()
        serializer = EmployeeTimelineSerializer(timeline, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def team(self, request, pk=None):
        employee = self.get_object()
        team = Employee.objects.filter(reporting_manager=employee)
        serializer = EmployeeListSerializer(team, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if query:
            employees = Employee.objects.filter(
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) | 
                Q(email__icontains=query) | 
                Q(employee_id__icontains=query) |
                Q(skills__icontains=query)
            )
            serializer = EmployeeListSerializer(employees, many=True)
            return Response(serializer.data)
        return Response([])

# class EmployeeDocumentViewSet(viewsets.ModelViewSet):
#     queryset = EmployeeDocument.objects.all()
#     serializer_class = EmployeeDocumentSerializer
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['employee', 'document_type', 'is_verified']
#     search_fields = ['title', 'description']
#     ordering_fields = ['title', 'created_at', 'expiry_date']
#     # permission_classes = [permissions.IsAuthenticated]

#     @action(detail=False, methods=['get'])
#     def expiring_soon(self, request):
#         from django.utils import timezone
#         from datetime import timedelta
        
#         days = int(request.query_params.get('days', 30))
#         future_date = timezone.now().date() + timedelta(days=days)
        
#         documents = EmployeeDocument.objects.filter(
#             expiry_date__isnull=False,
#             expiry_date__lte=future_date,
#             expiry_date__gte=timezone.now().date()
#         )
#         serializer = self.get_serializer(documents, many=True)
#         return Response(serializer.data)

class EmployeeEducationViewSet(viewsets.ModelViewSet):
    queryset = EmployeeEducation.objects.all()
    serializer_class = EmployeeEducationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'is_current']
    search_fields = ['institution', 'degree', 'field_of_study']
    ordering_fields = ['start_date', 'end_date']
    permission_classes = [permissions.IsAuthenticated]

class EmployeeExperienceViewSet(viewsets.ModelViewSet):
    queryset = EmployeeExperience.objects.all()
    serializer_class = EmployeeExperienceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'is_current']
    search_fields = ['company', 'title', 'description']
    ordering_fields = ['start_date', 'end_date']
    permission_classes = [permissions.IsAuthenticated]

class EmployeeSkillViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSkill.objects.all()
    serializer_class = EmployeeSkillSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'proficiency_level']
    search_fields = ['skill']
    ordering_fields = ['skill', 'proficiency_level']
    permission_classes = [permissions.IsAuthenticated]

class EmployeeTimelineViewSet(viewsets.ModelViewSet):
    queryset = EmployeeTimeline.objects.all()
    serializer_class = EmployeeTimelineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'event_type']
    search_fields = ['title', 'description']
    ordering_fields = ['event_date']
    permission_classes = [permissions.IsAuthenticated]

class EmployeeAttendanceViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAttendance.objects.all()
    serializer_class = EmployeeAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        employee_id = self.request.query_params.get('employee_id')
        date = self.request.query_params.get('date')
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if date:
            queryset = queryset.filter(date=date)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        employee = request.user.employee_profile
        today = timezone.now().date()
        
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'check_in': timezone.now()}
        )
        
        if not created and not attendance.check_in:
            attendance.check_in = timezone.now()
            attendance.save()
            
        serializer = self.get_serializer(attendance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        employee = request.user.employee_profile
        today = timezone.now().date()
        
        try:
            attendance = EmployeeAttendance.objects.get(
                employee=employee,
                date=today
            )
            attendance.check_out = timezone.now()
            attendance.calculate_total_hours()
            attendance.save()
            
            serializer = self.get_serializer(attendance)
            return Response(serializer.data)
        except EmployeeAttendance.DoesNotExist:
            return Response(
                {'error': 'No attendance record found for today'},
                status=status.HTTP_404_NOT_FOUND
            )

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        assigned_to = self.request.query_params.get('assigned_to')
        status = self.request.query_params.get('status')
        
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user.employee_profile)

class TaskTimeLogViewSet(viewsets.ModelViewSet):
    queryset = TaskTimeLog.objects.all()
    serializer_class = TaskTimeLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        employee_id = self.request.query_params.get('employee_id')
        task_id = self.request.query_params.get('task_id')
        date = self.request.query_params.get('date')
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if date:
            queryset = queryset.filter(start_time__date=date)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee_profile)

    @action(detail=False, methods=['post'])
    def start_time(self, request):
        task_id = request.data.get('task_id')
        try:
            task = Task.objects.get(id=task_id)
            time_log = TaskTimeLog.objects.create(
                task=task,
                employee=request.user.employee_profile,
                start_time=timezone.now()
            )
            serializer = self.get_serializer(time_log)
            return Response(serializer.data)
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def end_time(self, request, pk=None):
        time_log = self.get_object()
        if not time_log.end_time:
            time_log.end_time = timezone.now()
            time_log.calculate_hours_spent()
            time_log.save()
            
            serializer = self.get_serializer(time_log)
            return Response(serializer.data)
        return Response(
            {'error': 'Time log already ended'},
            status=status.HTTP_400_BAD_REQUEST
        )

class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data


        if user is not None:
            try:
                employee = user.employee_profile
                employee_id = str(employee.employee_id)
            except Exception:
                employee_id = None
            refresh = RefreshToken.for_user(user)
            # Determine role
            if user.is_superuser:
                role = 'admin'
            elif user.is_staff:
                role = 'staff'
            elif user.groups.exists():
                role = user.groups.first().name
            else:
                role = 'employee'
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'employee_id': employee_id,
                'role': role,
            })
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)