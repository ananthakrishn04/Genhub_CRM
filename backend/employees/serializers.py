# employees/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Department, Designation, Employee,
    EmployeeEducation, EmployeeExperience, EmployeeSkill, EmployeeTimeline
)

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