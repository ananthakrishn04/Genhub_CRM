from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .filters import EmployeeFilter

from .models import (
    Department, Designation, Employee,EmployeeEducation, 
    EmployeeExperience, EmployeeSkill, EmployeeTimeline
)
from .serializers import (
    DepartmentSerializer, DesignationSerializer, EmployeeListSerializer,
    EmployeeDetailSerializer, EmployeeCreateUpdateSerializer,
    EmployeeEducationSerializer, EmployeeExperienceSerializer, EmployeeSkillSerializer,
    EmployeeTimelineSerializer
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