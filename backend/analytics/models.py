from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import datetime, timedelta
import json


class Report(models.Model):
    REPORT_TYPES = [
        ('headcount', 'Headcount Report'),
        ('attrition', 'Attrition Report'),
        ('leave_utilization', 'Leave Utilization Report'),
        ('certificate_expiry', 'Certificate Expiry Report'),
        ('custom', 'Custom Report'),
    ]
    
    FREQUENCY_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once')
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Configuration
    filters = models.JSONField(default=dict, help_text="Filters applied to the report")
    columns = models.JSONField(default=list, help_text="Columns to include in the report")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Recipients for scheduled reports
    email_recipients = models.JSONField(default=list, help_text="Email addresses to send scheduled reports")
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ReportExecution(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='executions')
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # File storage
    file = models.FileField(
        upload_to='reports/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'xlsx', 'csv'])]
    )
    
    error_message = models.TextField(blank=True)
    execution_time = models.DurationField(null=True, blank=True)
    record_count = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.report.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class Certificate(models.Model):
    CERTIFICATE_TYPES = [
        ('professional', 'Professional Certification'),
        ('safety', 'Safety Certification'),
        ('compliance', 'Compliance Certificate'),
        ('training', 'Training Certificate'),
        ('license', 'License'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('expiring_soon', 'Expiring Soon'),
        ('pending_renewal', 'Pending Renewal'),
    ]
    
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='certificates')
    name = models.CharField(max_length=200)
    certificate_type = models.CharField(max_length=50, choices=CERTIFICATE_TYPES)
    issuing_authority = models.CharField(max_length=200)
    certificate_number = models.CharField(max_length=100, unique=True)
    
    issue_date = models.DateField()
    expiry_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # File storage
    certificate_file = models.FileField(
        upload_to='certificates/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    
    # Reminder settings
    reminder_days_before = models.IntegerField(default=30, help_text="Days before expiry to send reminder")
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['expiry_date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.name}"
    
    @property
    def days_until_expiry(self):
        return (self.expiry_date - timezone.now().date()).days
    
    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()
    
    @property
    def is_expiring_soon(self):
        return 0 <= self.days_until_expiry <= self.reminder_days_before
    
    def update_status(self):
        if self.is_expired:
            self.status = 'expired'
        elif self.is_expiring_soon:
            self.status = 'expiring_soon'
        else:
            self.status = 'active'
        self.save(update_fields=['status'])


class HRMetric(models.Model):
    METRIC_TYPES = [
        ('headcount', 'Headcount'),
        ('attrition_rate', 'Attrition Rate'),
        ('average_tenure', 'Average Tenure'),
        ('new_hires', 'New Hires'),
        ('terminations', 'Terminations'),
        ('leave_utilization', 'Leave Utilization'),
        ('diversity_ratio', 'Diversity Ratio'),
        ('promotion_rate', 'Promotion Rate'),
    ]
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    percentage_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Time dimension
    date = models.DateField()
    month = models.IntegerField()
    year = models.IntegerField()
    quarter = models.IntegerField()
    
    # Dimensional breakdowns
    department = models.ForeignKey('employees.Department', on_delete=models.CASCADE, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Metadata
    calculation_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['metric_type', 'date', 'department']
        ordering = ['-date', 'metric_type']
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.date}"
