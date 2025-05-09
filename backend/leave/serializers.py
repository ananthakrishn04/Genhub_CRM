from rest_framework import serializers
from .models import LeaveType, LeavePolicy, LeaveBalance, LeaveRequest, LeaveComment, Holiday
from employees.serializers import EmployeeListSerializer

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_name = serializers.ReadOnlyField(source='leave_type.name')
    department_name = serializers.ReadOnlyField(source='department.name')
    designation_title = serializers.ReadOnlyField(source='designation.title')
    
    class Meta:
        model = LeavePolicy
        fields = '__all__'

class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.full_name')
    leave_type_name = serializers.ReadOnlyField(source='leave_type.name')
    available_days = serializers.ReadOnlyField()
    
    class Meta:
        model = LeaveBalance
        fields = '__all__'

class LeaveCommentSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.full_name')
    
    class Meta:
        model = LeaveComment
        fields = '__all__'

class LeaveRequestListSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.full_name')
    leave_type_name = serializers.ReadOnlyField(source='leave_type.name')
    number_of_days = serializers.ReadOnlyField()
    
    class Meta:
        model = LeaveRequest
        fields = ['id', 'employee', 'employee_name', 'leave_type', 'leave_type_name', 
                  'start_date', 'end_date', 'number_of_days', 'status', 'created_at']

class LeaveRequestDetailSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer(read_only=True)
    leave_type_name = serializers.ReadOnlyField(source='leave_type.name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.full_name')
    number_of_days = serializers.ReadOnlyField()
    comments = LeaveCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = '__all__'

class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 
                  'half_day', 'half_day_type', 'reason', 'status']
        
    def validate(self, data):
        # Check if end_date is not before start_date
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError({'end_date': 'End date cannot be before start date'})
            
        # Check if half_day_type is provided when half_day is True
        if data.get('half_day', False) and not data.get('half_day_type'):
            raise serializers.ValidationError({'half_day_type': 'Half day type must be specified when half day is selected'})
            
        return data

class LeaveRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['status', 'approved_by', 'rejection_reason']
        
    def validate(self, data):
        if data.get('status') == 'REJECTED' and not data.get('rejection_reason'):
            raise serializers.ValidationError({'rejection_reason': 'Rejection reason is required when rejecting a leave request'})
        return data

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'