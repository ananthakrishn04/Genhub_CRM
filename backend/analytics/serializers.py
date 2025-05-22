from rest_framework import serializers
from .models import Report, ReportExecution, Certificate, HRMetric


class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    execution_count = serializers.SerializerMethodField()
    last_execution = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_execution_count(self, obj):
        return obj.executions.count()
    
    def get_last_execution(self, obj):
        last_execution = obj.executions.first()
        if last_execution:
            return {
                'id': last_execution.id,
                'status': last_execution.status,
                'started_at': last_execution.started_at,
                'completed_at': last_execution.completed_at,
            }
        return None


class ReportExecutionSerializer(serializers.ModelSerializer):
    report_name = serializers.CharField(source='report.name', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportExecution
        fields = '__all__'
        read_only_fields = ['executed_by', 'started_at', 'completed_at', 'execution_time']
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class CertificateSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    days_until_expiry = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    is_expiring_soon = serializers.ReadOnlyField()
    
    class Meta:
        model = Certificate
        fields = '__all__'
        read_only_fields = ['status', 'reminder_sent', 'reminder_sent_date', 'created_at', 'updated_at']


class HRMetricSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    
    class Meta:
        model = HRMetric
        fields = '__all__'
        read_only_fields = ['created_at']