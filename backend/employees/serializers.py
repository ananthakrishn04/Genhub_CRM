from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import (
    Department, Designation, Employee, EmployeeEducation, 
    EmployeeExperience, EmployeeSkill, EmployeeTimeline, EmployeeAttendance, TaskTimeLog
)

from boarding.models import Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class DesignationSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    
    class Meta:
        model = Designation
        fields = '__all__'

class EmployeeEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEducation
        fields = '__all__'

class EmployeeExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeExperience
        fields = '__all__'

class EmployeeSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSkill
        fields = '__all__'

class EmployeeTimelineSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = EmployeeTimeline
        fields = '__all__'

class EmployeeListSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    designation_title = serializers.ReadOnlyField(source='designation.title')
    
    class Meta:
        model = Employee
        fields = ['employee_id', 'first_name', 'last_name', 
                 'email', 'profile_picture', 'department', 'department_name', 
                 'designation', 'designation_title', 'employment_status', 'is_active']

class EmployeeDetailSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    designation_title = serializers.ReadOnlyField(source='designation.title')
    reporting_manager_name = serializers.ReadOnlyField(source='reporting_manager.full_name')
    education = EmployeeEducationSerializer(many=True, read_only=True)
    experiences = EmployeeExperienceSerializer(many=True, read_only=True)
    skill_list = EmployeeSkillSerializer(many=True, read_only=True)
    timeline = EmployeeTimelineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeAttendance
        fields = '__all__'
        read_only_fields = ('total_hours',)

    def get_employee_name(self, obj):
        return obj.employee.full_name

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.full_name

    def get_assigned_by_name(self, obj):
        return obj.assigned_by.full_name

class TaskTimeLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    task_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskTimeLog
        fields = '__all__'
        read_only_fields = ('hours_spent',)

    def get_employee_name(self, obj):
        return obj.employee.full_name

    def get_task_name(self, obj):
        return obj.task.name
    

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        return user