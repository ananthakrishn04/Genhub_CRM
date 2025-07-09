from rest_framework import serializers
from .models import (
    ProcessTemplate, TaskTemplate, Process, 
    Task, Equipment, EquipmentAssignment
)
from employees.serializers import EmployeeListSerializer, DepartmentSerializer


class TaskTemplateSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    
    class Meta:
        model = TaskTemplate
        fields = '__all__'


class ProcessTemplateListSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessTemplate
        fields = ['id', 'name', 'process_type', 'is_active', 'task_count']
    
    def get_task_count(self, obj):
        return obj.task_templates.count()


class ProcessTemplateDetailSerializer(serializers.ModelSerializer):
    task_templates = TaskTemplateSerializer(many=True, read_only=True)
    departments = DepartmentSerializer(many=True, read_only=True)
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = ProcessTemplate
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    assignee_name = serializers.SerializerMethodField()
    completed_by_name = serializers.ReadOnlyField(source='completed_by.get_full_name')
    dependencies = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = '__all__'
    
    def get_assignee_name(self, obj):
        return obj.assignee.full_name if obj.assignee else None
    
    def get_dependencies(self, obj):
        return [{'id': task.id, 'name': task.name} for task in obj.depends_on.all()]


class ProcessListSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.full_name')
    completion_percentage = serializers.ReadOnlyField()
    task_count = serializers.SerializerMethodField()
    template_name = serializers.ReadOnlyField(source='process_template.name')
    
    class Meta:
        model = Process
        fields = [
            'id', 'employee', 'employee_name', 'process_type', 
            'status', 'start_date', 'target_completion_date', 
            'completion_percentage', 'task_count', 'template_name'
        ]
    
    def get_task_count(self, obj):
        return obj.process_tasks.count()


class ProcessDetailSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer(read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    completion_percentage = serializers.ReadOnlyField()
    template_name = serializers.ReadOnlyField(source='process_template.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = Process
        fields = '__all__'


class EquipmentSerializer(serializers.ModelSerializer):
    current_assignment = serializers.SerializerMethodField()
    
    class Meta:
        model = Equipment
        fields = '__all__'
    
    def get_current_assignment(self, obj):
        current = obj.assignments.filter(actual_return_date__isnull=True).first()
        if current:
            return {
                'id': current.id,
                'employee_id': current.employee.id,
                'employee_name': current.employee.full_name,
                'assigned_date': current.assigned_date
            }
        return None


class EquipmentAssignmentSerializer(serializers.ModelSerializer):
    equipment_name = serializers.ReadOnlyField(source='equipment.name')
    equipment_type = serializers.ReadOnlyField(source='equipment.type')
    employee_name = serializers.ReadOnlyField(source='employee.full_name')
    assigned_by_name = serializers.ReadOnlyField(source='assigned_by.get_full_name')
    received_by_name = serializers.ReadOnlyField(source='received_by.get_full_name') 
    
    class Meta:
        model = EquipmentAssignment
        fields = '__all__'