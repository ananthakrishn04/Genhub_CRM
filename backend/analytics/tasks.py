from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import ReportExecution, Certificate
from .utils import ReportGenerator
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_report_task(execution_id):
    """Celery task to generate report files"""
    try:
        execution = ReportExecution.objects.get(id=execution_id)
        execution.status = 'running'
        execution.save()
        
        generator = ReportGenerator()
        report_data = generator.get_report_data(execution.report)
        
        # Generate file based on format
        if execution.report.format == 'pdf':
            file_buffer = generator.generate_pdf(report_data, execution.report.name)
            filename = f"{execution.report.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        elif execution.report.format == 'excel':
            file_buffer = generator.generate_excel(report_data, execution.report.name)
            filename = f"{execution.report.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        else:  # csv
            import csv
            import io
            file_buffer = io.StringIO()
            writer = csv.DictWriter(file_buffer, fieldnames=report_data['columns'])
            writer.writeheader()
            writer.writerows(report_data['data'])
            file_buffer.seek(0)
            filename = f"{execution.report.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Save file
        execution.file.save(filename, file_buffer, save=False)
        execution.status = 'completed'
        execution.completed_at = timezone.now()
        execution.record_count = report_data['total_records']
        execution.execution_time = execution.completed_at - execution.started_at
        execution.save()
        
        # Send email if recipients specified
        if execution.report.email_recipients:
            send_report_email.delay(execution.id)
        
        logger.info(f"Report generation completed for execution {execution_id}")
        
    except Exception as e:
        execution = ReportExecution.objects.get(id=execution_id)
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save()
        
        logger.error(f"Report generation failed for execution {execution_id}: {str(e)}")


@shared_task
def send_report_email(execution_id):
    """Send generated report via email"""
    try:
        execution = ReportExecution.objects.get(id=execution_id)
        
        if not execution.file:
            return
        
        subject = f"Report: {execution.report.name}"
        message = render_to_string('analytics/report_email.html', {
            'report': execution.report,
            'execution': execution,
        })
        
        # Send email with attachment
        from django.core.mail import EmailMessage
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=execution.report.email_recipients,
        )
        email.content_subtype = 'html'
        email.attach_file(execution.file.path)
        email.send()
        
        logger.info(f"Report email sent for execution {execution_id}")
        
    except Exception as e:
        logger.error(f"Failed to send report email for execution {execution_id}: {str(e)}")


@shared_task
def send_certificate_reminders(days_before=30):
    """Send certificate expiry reminders"""
    try:
        cutoff_date = timezone.now().date() + timedelta(days=days_before)
        
        certificates = Certificate.objects.filter(
            expiry_date__lte=cutoff_date,
            expiry_date__gte=timezone.now().date(),
            reminder_sent=False
        )
        
        for cert in certificates:
            subject = f"Certificate Expiry Reminder: {cert.name}"
            message = render_to_string('analytics/certificate_reminder_email.html', {
                'certificate': cert,
                'employee': cert.employee,
            })
            
            # Send to employee and HR
            recipients = [cert.employee.email]
            if hasattr(settings, 'HR_EMAIL'):
                recipients.append(settings.HR_EMAIL)
            
            send_mail(
                subject=subject,
                message='',
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
            
            # Mark reminder as sent
            cert.reminder_sent = True
            cert.reminder_sent_date = timezone.now()
            cert.save()
        
        logger.info(f"Certificate reminders sent for {certificates.count()} certificates")
        
    except Exception as e:
        logger.error(f"Failed to send certificate reminders: {str(e)}")


@shared_task
def update_certificate_statuses():
    """Update certificate statuses based on expiry dates"""
    try:
        certificates = Certificate.objects.all()
        updated_count = 0
        
        for cert in certificates:
            old_status = cert.status
            cert.update_status()
            if cert.status != old_status:
                updated_count += 1
        
        logger.info(f"Updated status for {updated_count} certificates")
        
    except Exception as e:
        logger.error(f"Failed to update certificate statuses: {str(e)}")


@shared_task
def generate_scheduled_reports():
    """Generate scheduled reports that are due"""
    from .models import Report
    
    try:
        now = timezone.now()
        due_reports = Report.objects.filter(
            is_scheduled=True,
            is_active=True,
            next_run__lte=now
        )
        
        for report in due_reports:
            # Create execution
            execution = ReportExecution.objects.create(
                report=report,
                status='pending'
            )
            
            # Queue generation task
            generate_report_task.delay(execution.id)
            
            # Update next run time
            report.next_run = calculate_next_run_time(report.frequency, now)
            report.save()
        
        logger.info(f"Queued {due_reports.count()} scheduled reports")
        
    except Exception as e:
        logger.error(f"Failed to process scheduled reports: {str(e)}")


def calculate_next_run_time(frequency, current_time):
    """Calculate next run time based on frequency"""
    if frequency == 'daily':
        return current_time + timedelta(days=1)
    elif frequency == 'weekly':
        return current_time + timedelta(weeks=1)
    elif frequency == 'monthly':
        return current_time + timedelta(days=30)  # Approximate
    elif frequency == 'quarterly':
        return current_time + timedelta(days=90)  # Approximate
    elif frequency == 'yearly':
        return current_time + timedelta(days=365)  # Approximate
    else:
        return None