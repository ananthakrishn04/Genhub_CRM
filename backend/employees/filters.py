from django_filters import rest_framework as filters
from .models import Employee

class EmployeeFilter(filters.FilterSet):
    department_name = filters.CharFilter(field_name='department__name', lookup_expr='icontains')
    designation = filters.CharFilter(field_name='designation__title', lookup_expr='icontains')
    
    class Meta:
        model = Employee
        fields = ['is_active','employment_status', 'employment_type']