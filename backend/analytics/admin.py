from django.contrib import admin
from .models import Report, ReportExecution, Certificate, HRMetric


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'is_scheduled', 'frequency', 'is_active', 'created_at']
    list_filter = ['report_type', 'is_scheduled', 'frequency', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'report_type', 'created_by')
        }),
        ('Configuration', {
            'fields': ('filters', 'columns', 'format')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'frequency', 'next_run', 'email_recipients')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )


@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = ['report', 'status', 'executed_by', 'started_at', 'completed_at', 'record_count']
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = ['report__name']
    readonly_fields = ['started_at', 'completed_at', 'execution_time']
    
    def has_add_permission(self, request):
        return False


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee', 'certificate_type', 'expiry_date', 'status', 'days_until_expiry']
    list_filter = ['certificate_type', 'status', 'expiry_date', 'created_at']
    search_fields = ['name', 'employee__first_name', 'employee__last_name', 'certificate_number']
    readonly_fields = ['status', 'days_until_expiry', 'is_expired', 'is_expiring_soon', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Certificate Information', {
            'fields': ('employee', 'name', 'certificate_type', 'issuing_authority', 'certificate_number')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date')
        }),
        ('File & Status', {
            'fields': ('certificate_file', 'status')
        }),
        ('Reminders', {
            'fields': ('reminder_days_before', 'reminder_sent', 'reminder_sent_date')
        }),
        ('Calculated Fields', {
            'fields': ('days_until_expiry', 'is_expired', 'is_expiring_soon'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_expiry_reminders', 'update_statuses']
    
    def send_expiry_reminders(self, request, queryset):
        from .tasks import send_certificate_reminders
        send_certificate_reminders.delay()
        self.message_user(request, "Certificate reminder task has been queued.")
    send_expiry_reminders.short_description = "Send expiry reminders for selected certificates"
    
    def update_statuses(self, request, queryset):
        for cert in queryset:
            cert.update_status()
        self.message_user(request, f"Updated status for {queryset.count()} certificates.")
    update_statuses.short_description = "Update status for selected certificates"


@admin.register(HRMetric)
class HRMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'percentage_value', 'date', 'department', 'created_at']
    list_filter = ['metric_type', 'date', 'department', 'year', 'quarter']
    search_fields = ['metric_type']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('metric_type', 'value', 'percentage_value')
        }),
        ('Time Dimension', {
            'fields': ('date', 'month', 'year', 'quarter')
        }),
        ('Dimensions', {
            'fields': ('department', 'location')
        }),
        ('Details', {
            'fields': ('calculation_details', 'created_at'),
            'classes': ('collapse',)
        })
    )