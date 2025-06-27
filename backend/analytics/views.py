from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponse
from .models import Report, ReportExecution, Certificate, HRMetric
from .serializers import (
    ReportSerializer, ReportExecutionSerializer, 
    CertificateSerializer, HRMetricSerializer
)
from .utils import ReportGenerator, MetricsCalculator
from .tasks import generate_report_task, send_certificate_reminders


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a report immediately"""
        report = self.get_object()
        
        # Create execution record
        execution = ReportExecution.objects.create(
            report=report,
            executed_by=request.user.employee_profile,
            status='pending'
        )
        
        # Queue the report generation task
        generate_report_task.delay(execution.id)
        
        return Response({
            'execution_id': execution.id,
            'message': 'Report generation started'
        })
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Preview report data without generating file"""
        report = self.get_object()
        generator = ReportGenerator()
        
        try:
            data = generator.get_report_data(report)
            return Response({
                'columns': data.get('columns', []),
                'data': data.get('data', [])[:10],  # First 10 records for preview
                'total_records': len(data.get('data', []))
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """Get available report templates"""
        templates = [
            {
                'type': 'headcount',
                'name': 'Headcount Report',
                'description': 'Employee count by department, location, status',
                'default_columns': ['employee_id', 'full_name', 'department', 'designation', 'hire_date', 'status']
            },
            {
                'type': 'attrition',
                'name': 'Attrition Report',
                'description': 'Employee turnover analysis',
                'default_columns': ['employee_id', 'full_name', 'department', 'hire_date', 'termination_date', 'reason']
            },
            {
                'type': 'leave_utilization',
                'name': 'Leave Utilization Report',
                'description': 'Leave usage patterns and balances',
                'default_columns': ['employee_id', 'full_name', 'leave_type', 'total_days', 'used_days', 'balance']
            },
            {
                'type': 'certificate_expiry',
                'name': 'Certificate Expiry Report',
                'description': 'Upcoming certificate expirations',
                'default_columns': ['employee_id', 'employee_name', 'certificate_name', 'expiry_date', 'days_until_expiry']
            }
        ]
        return Response(templates)


class ReportExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportExecution.objects.all()
    serializer_class = ReportExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        report_id = self.request.query_params.get('report_id')
        if report_id:
            queryset = queryset.filter(report_id=report_id)
        return queryset
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download generated report file"""
        execution = self.get_object()
        
        if not execution.file:
            return Response({
                'error': 'No file available for this execution'
            }, status=status.HTTP_404_NOT_FOUND)
        
        response = HttpResponse(
            execution.file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{execution.file.name}"'
        return response


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by expiry date range
        expiry_from = self.request.query_params.get('expiry_from')
        expiry_to = self.request.query_params.get('expiry_to')
        
        if expiry_from:
            queryset = queryset.filter(expiry_date__gte=expiry_from)
        if expiry_to:
            queryset = queryset.filter(expiry_date__lte=expiry_to)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get certificates expiring within specified days"""
        days = int(request.query_params.get('days', 30))
        cutoff_date = timezone.now().date() + timedelta(days=days)
        
        certificates = self.get_queryset().filter(
            expiry_date__lte=cutoff_date,
            expiry_date__gte=timezone.now().date()
        ).order_by('expiry_date')
        
        serializer = self.get_serializer(certificates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def send_reminders(self, request):
        """Send certificate expiry reminders"""
        days = int(request.data.get('days', 30))
        send_certificate_reminders.delay(days)
        
        return Response({
            'message': f'Certificate reminder task queued for certificates expiring within {days} days'
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get certificate statistics"""
        total = self.get_queryset().count()
        expired = self.get_queryset().filter(status='expired').count()
        expiring_soon = self.get_queryset().filter(status='expiring_soon').count()
        active = self.get_queryset().filter(status='active').count()
        
        # By type
        by_type = self.get_queryset().values('certificate_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total': total,
            'expired': expired,
            'expiring_soon': expiring_soon,
            'active': active,
            'by_type': list(by_type)
        })


class HRMetricViewSet(viewsets.ModelViewSet):
    queryset = HRMetric.objects.all()
    serializer_class = HRMetricSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by metric type
        metric_type = self.request.query_params.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Filter by department
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard metrics for specified time period"""
        # Default to last 12 months
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        # Override with query params if provided
        if request.query_params.get('start_date'):
            start_date = datetime.strptime(request.query_params.get('start_date'), '%Y-%m-%d').date()
        if request.query_params.get('end_date'):
            end_date = datetime.strptime(request.query_params.get('end_date'), '%Y-%m-%d').date()
        
        metrics = self.get_queryset().filter(
            date__range=[start_date, end_date]
        )
        
        # Group metrics by type
        dashboard_data = {}
        
        for metric_type, _ in HRMetric.METRIC_TYPES:
            metric_data = metrics.filter(metric_type=metric_type).order_by('date')
            
            dashboard_data[metric_type] = {
                'current_value': metric_data.last().value if metric_data.exists() else 0,
                'trend_data': [
                    {
                        'date': m.date.isoformat(),
                        'value': float(m.value),
                        'percentage_value': float(m.percentage_value) if m.percentage_value else None
                    }
                    for m in metric_data
                ]
            }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Trigger metrics calculation for specified date range"""
        calculator = MetricsCalculator()
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        try:
            calculator.calculate_all_metrics(start_date, end_date)
            return Response({
                'message': 'Metrics calculation completed successfully'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)