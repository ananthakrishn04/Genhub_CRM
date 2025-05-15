from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction

from .models import (
    ProcessTemplate, TaskTemplate, Process, 
    Task, Equipment, EquipmentAssignment
)
from .serializers import (
    ProcessTemplateListSerializer, ProcessTemplateDetailSerializer,
    TaskTemplateSerializer, ProcessListSerializer, ProcessDetailSerializer,
    TaskSerializer, EquipmentSerializer, EquipmentAssignmentSerializer
)


class ProcessTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProcessTemplate.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['process_type', 'is_active', 'departments']
    search_fields = ['name', 'description']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessTemplateListSerializer
        return ProcessTemplateDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        original_template = self.get_object()
        with transaction.atomic():
            # Clone the template
            new_template = ProcessTemplate.objects.create(
                name=f"Copy of {original_template.name}",
                process_type=original_template.process_type,
                description=original_template.description,
                is_active=original_template.is_active,
                created_by=request.user
            )
            
            # Clone the departments
            new_template.departments.set(original_template.departments.all())
            
            # Clone task templates
            task_templates = original_template.task_templates.all()
            task_template_mapping = {}  # To keep track of original ID to new object
            
            # First pass: create all task templates without dependencies
            for task_template in task_templates:
                new_task = TaskTemplate.objects.create(
                    process_template=new_template,
                    name=task_template.name,
                    description=task_template.description,
                    department=task_template.department,
                    assignee_role=task_template.assignee_role,
                    estimated_days=task_template.estimated_days,
                    priority=task_template.priority,
                    is_mandatory=task_template.is_mandatory,
                    order=task_template.order
                )
                task_template_mapping[task_template.id] = new_task
            
            # Second pass: set up dependencies
            for task_template in task_templates:
                if task_template.depends_on.exists():
                    new_task = task_template_mapping[task_template.id]
                    for dependency in task_template.depends_on.all():
                        if dependency.id in task_template_mapping:
                            new_task.depends_on.add(task_template_mapping[dependency.id])
        
        return Response(
            ProcessTemplateDetailSerializer(new_template, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class TaskTemplateViewSet(viewsets.ModelViewSet):
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['process_template', 'department', 'is_mandatory']


class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['employee', 'process_type', 'status', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'notes']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessListSerializer
        return ProcessDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_process(self, request, pk=None):
        process = self.get_object()
        
        if process.status != 'planned':
            return Response(
                {"error": "Process must be in 'planned' status to start"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update process status
        process.status = 'in_progress'
        process.save()
        
        # Optional: Update tasks status based on dependencies
        for task in process.tasks.filter(depends_on__isnull=True):
            task.status = 'in_progress'
            task.save()
        
        return Response({"message": "Process started successfully"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def complete_process(self, request, pk=None):
        process = self.get_object()
        
        # Check if all mandatory tasks are completed
        incomplete_mandatory_tasks = process.tasks.filter(
            is_mandatory=True
        ).exclude(status='completed').count()
        
        if incomplete_mandatory_tasks > 0:
            return Response(
                {"error": f"Cannot complete process. {incomplete_mandatory_tasks} mandatory tasks are still incomplete."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update process status
        process.status = 'completed'
        process.actual_completion_date = timezone.now().date()
        process.save()
        
        return Response({"message": "Process completed successfully"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def generate_tasks_from_template(self, request, pk=None):
        process = self.get_object()
        template_id = request.data.get('template_id')
        
        if not template_id:
            return Response(
                {"error": "template_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            template = ProcessTemplate.objects.get(pk=template_id)
        except ProcessTemplate.DoesNotExist:
            return Response(
                {"error": "Template not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update process with template
        process.process_template = template
        process.save()
        
        # Create tasks from template
        with transaction.atomic():
            task_template_mapping = {}  # For handling dependencies
            
            for task_template in template.task_templates.all():
                task = Task.objects.create(
                    process=process,
                    task_template=task_template,
                    name=task_template.name,
                    description=task_template.description,
                    department=task_template.department,
                    priority=task_template.priority,
                    is_mandatory=task_template.is_mandatory,
                    order=task_template.order
                )
                task_template_mapping[task_template.id] = task
            
            # Set up dependencies between tasks
            for task_template in template.task_templates.all():
                if task_template.depends_on.exists():
                    task = task_template_mapping[task_template.id]
                    for dependency in task_template.depends_on.all():
                        if dependency.id in task_template_mapping:
                            task.depends_on.add(task_template_mapping[dependency.id])
        
        return Response({"message": "Tasks generated successfully"}, status=status.HTTP_200_OK)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['process', 'department', 'assignee', 'status', 'priority', 'is_mandatory']
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        task = self.get_object()
        notes = request.data.get('completion_notes', '')
        
        task.status = 'completed'
        task.completion_date = timezone.now().date()
        task.completion_notes = notes
        task.completed_by = request.user
        task.save()
        
        # Check for dependent tasks that can now be started
        dependent_tasks = Task.objects.filter(depends_on=task, status='not_started')
        for dependent_task in dependent_tasks:
            # Check if all dependencies are completed
            if all(dep.status == 'completed' for dep in dependent_task.depends_on.all()):
                dependent_task.status = 'in_progress'
                dependent_task.save()
        
        return Response({"message": "Task completed successfully"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def assign_task(self, request, pk=None):
        task = self.get_object()
        assignee_id = request.data.get('assignee_id')
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            assignee = User.objects.get(pk=assignee_id)
            task.assignee = assignee
            task.save()
            return Response({"message": "Task assigned successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'status']
    search_fields = ['name', 'identifier', 'description']
    
    @action(detail=True, methods=['post'])
    def assign_equipment(self, request, pk=None):
        equipment = self.get_object()
        employee_id = request.data.get('employee_id')
        assigned_date = request.data.get('assigned_date')
        expected_return_date = request.data.get('expected_return_date', None)
        condition = request.data.get('condition', '')
        notes = request.data.get('notes', '')
        
        if equipment.status != 'available':
            return Response(
                {"error": "Equipment is not available for assignment"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from employee_management.models import Employee
            employee = Employee.objects.get(pk=employee_id)
            
            # Create equipment assignment
            assignment = EquipmentAssignment.objects.create(
                equipment=equipment,
                employee=employee,
                assigned_date=assigned_date,
                expected_return_date=expected_return_date,
                condition_on_assignment=condition,
                assigned_by=request.user,
                notes=notes
            )
            
            # Update equipment status
            equipment.status = 'assigned'
            equipment.save()
            
            return Response(
                EquipmentAssignmentSerializer(assignment).data,
                status=status.HTTP_201_CREATED
            )
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)


class EquipmentAssignmentViewSet(viewsets.ModelViewSet):
    queryset = EquipmentAssignment.objects.all()
    serializer_class = EquipmentAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['equipment', 'employee', 'assigned_date']
    
    @action(detail=True, methods=['post'])
    def return_equipment(self, request, pk=None):
        assignment = self.get_object()
        return_date = request.data.get('return_date')
        condition = request.data.get('condition', '')
        
        if assignment.actual_return_date:
            return Response(
                {"error": "Equipment has already been returned"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update assignment
        assignment.actual_return_date = return_date
        assignment.condition_on_return = condition
        assignment.received_by = request.user
        assignment.save()
        
        # Update equipment status
        equipment = assignment.equipment
        equipment.status = 'available'
        equipment.save()
        
        return Response({"message": "Equipment returned successfully"}, status=status.HTTP_200_OK)