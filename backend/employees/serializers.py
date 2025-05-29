from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Department, Designation, Employee, EmployeeEducation, 
    EmployeeExperience, EmployeeSkill, EmployeeTimeline
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

from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import (
    Department, Designation, Employee, EmployeeEducation, 
    EmployeeExperience, EmployeeSkill, EmployeeTimeline
)

class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    # Exclude user field from input - we'll handle it automatically
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # Optional fields for user creation
    username = serializers.CharField(write_only=True, required=False, help_text="Username for the user account. If not provided, will be generated from email.")
    password = serializers.CharField(write_only=True, required=False, help_text="Password for the user account. If not provided, a default password will be set.")
    
    class Meta:
        model = Employee
        fields = '__all__'
    
    def validate_email(self, value):
        """Validate email uniqueness across both User and Employee models"""
        # Check if email exists in User model (excluding current user if updating)
        user_query = User.objects.filter(email=value)
        if self.instance and hasattr(self.instance, 'user'):
            user_query = user_query.exclude(id=self.instance.user.id)
        
        if user_query.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        # Check if email exists in Employee model (excluding current instance if updating)
        employee_query = Employee.objects.filter(email=value)
        if self.instance:
            employee_query = employee_query.exclude(employee_id=self.instance.employee_id)
        
        if employee_query.exists():
            raise serializers.ValidationError("An employee with this email already exists.")
        
        return value
    
    def generate_username(self, email, first_name, last_name):
        """Generate a unique username"""
        # Try email prefix first
        base_username = email.split('@')[0].lower()
        
        # If that fails, try first_name.last_name
        if User.objects.filter(username=base_username).exists():
            base_username = f"{first_name.lower()}.{last_name.lower()}"
        
        # If still not unique, add numbers
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    @transaction.atomic
    def create(self, validated_data):
        """Create Employee with associated User"""
        # Extract user-related data
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        
        # Generate username if not provided
        if not username:
            username = self.generate_username(
                validated_data['email'],
                validated_data['first_name'],
                validated_data['last_name']
            )
        
        # Set default password if not provided
        if not password:
            password = 'TempPass123!'  # You might want to generate a random password
        
        # Create the User
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=password,
            is_active=validated_data.get('is_active', True)
        )
        
        # Create the Employee with the user
        validated_data['user'] = user
        employee = Employee.objects.create(**validated_data)
        
        return employee
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update Employee and associated User"""
        # Extract user-related data
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        
        # Update the associated User
        user = instance.user
        user.email = validated_data.get('email', user.email)
        user.first_name = validated_data.get('first_name', user.first_name)
        user.last_name = validated_data.get('last_name', user.last_name)
        user.is_active = validated_data.get('is_active', user.is_active)
        
        if username:
            # Check if username is available (excluding current user)
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                raise serializers.ValidationError({"username": "This username is already taken."})
            user.username = username
        
        if password:
            user.set_password(password)
        
        user.save()
        
        # Update the Employee
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        """Customize the output representation"""
        data = super().to_representation(instance)
        
        # Add user information to the response
        if instance.user:
            data['user_info'] = {
                'id': instance.user.id,
                'username': instance.user.username,
                'email': instance.user.email,
                'is_active': instance.user.is_active,
                'date_joined': instance.user.date_joined
            }
        
        return data