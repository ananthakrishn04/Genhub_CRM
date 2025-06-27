import pandas as pd
from django.db.models import Count, Avg, Q, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from io import BytesIO
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from employees.models import Employee, Department
from leave.models import LeaveRequest, LeaveBalance
from .models import Certificate, HRMetric


class ReportGenerator:
    """Utility class for generating various types of reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def get_report_data(self, report):
        """Get data for a specific report based on its type and filters"""
        if report.report_type == 'headcount':
            return self._get_headcount_data(report)
        elif report.report_type == 'attrition':
            return self._get_attrition_data(report)
        elif report.report_type == 'leave_utilization':
            return self._get_leave_utilization_data(report)
        elif report.report_type == 'certificate_expiry':
            return self._get_certificate_expiry_data(report)
        else:
            raise ValueError(f"Unknown report type: {report.report_type}")
    
    def _get_headcount_data(self, report):
        """Generate headcount report data"""
        queryset = Employee.objects.all()
        
        # Apply filters
        filters = report.filters
        if filters.get('department_id'):
            queryset = queryset.filter(department_id=filters['department_id'])
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        if filters.get('hire_date_from'):
            queryset = queryset.filter(hire_date__gte=filters['hire_date_from'])
        if filters.get('hire_date_to'):
            queryset = queryset.filter(hire_date__lte=filters['hire_date_to'])
        
        # Select columns
        columns = report.columns or ['employee_id', 'full_name', 'department', 'designation', 'hire_date', 'status']
        
        data = []
        for employee in queryset.select_related('department', 'designation'):
            row = {}
            for col in columns:
                if col == 'employee_id':
                    row[col] = employee.employee_id
                elif col == 'full_name':
                    row[col] = employee.full_name
                elif col == 'department':
                    row[col] = employee.department.name if employee.department else ''
                elif col == 'designation':
                    row[col] = employee.designation.title if employee.designation else ''
                elif col == 'hire_date':
                    row[col] = employee.date_of_joining.isoformat() if employee.date_of_joining else ''
                elif col == 'status':
                    row[col] = employee.is_active
                else:
                    row[col] = getattr(employee, col, '')
            data.append(row)
        
        return {
            'columns': columns,
            'data': data,
            'total_records': len(data)
        }
    
    def _get_certificate_expiry_data(self, report):
        """Generate certificate expiry report data"""
        queryset = Certificate.objects.select_related('employee')
        
        # Apply filters
        filters = report.filters
        if filters.get('days_until_expiry'):
            cutoff_date = timezone.now().date() + timedelta(days=int(filters['days_until_expiry']))
            queryset = queryset.filter(expiry_date__lte=cutoff_date, expiry_date__gte=timezone.now().date())
        
        if filters.get('certificate_type'):
            queryset = queryset.filter(certificate_type=filters['certificate_type'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        columns = report.columns or ['employee_id', 'employee_name', 'certificate_name', 'certificate_type', 'expiry_date', 'days_until_expiry']
        
        data = []
        for cert in queryset:
            row = {}
            for col in columns:
                if col == 'employee_id':
                    row[col] = cert.employee.employee_id
                elif col == 'employee_name':
                    row[col] = cert.employee.full_name
                elif col == 'certificate_name':
                    row[col] = cert.name
                elif col == 'certificate_type':
                    row[col] = cert.get_certificate_type_display()
                elif col == 'expiry_date':
                    row[col] = cert.expiry_date.isoformat()
                elif col == 'days_until_expiry':
                    row[col] = cert.days_until_expiry
                else:
                    row[col] = getattr(cert, col, '')
            data.append(row)
        
        return {
            'columns': columns,
            'data': data,
            'total_records': len(data)
        }
    
    def generate_pdf(self, report_data, title="Report"):
        """Generate PDF report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title_para = Paragraph(title, self.styles['Title'])
        story.append(title_para)
        
        # Table data
        table_data = [report_data['columns']]  # Header
        table_data.extend([list(row.values()) for row in report_data['data']])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        
        buffer.seek(0)
        return buffer
    
    def generate_excel(self, report_data, title="Report"):
        """Generate Excel report"""
        buffer = BytesIO()
        
        # Create DataFrame
        df = pd.DataFrame(report_data['data'])
        
        # Write to Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=title, index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[title]
            
            # Format header
            for cell in worksheet[1]:
                cell.font = openpyxl.styles.Font(bold=True)
                cell.fill = openpyxl.styles.PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        buffer.seek(0)
        return buffer


class MetricsCalculator:
    """Utility class for calculating HR metrics"""
    
    def calculate_all_metrics(self, start_date=None, end_date=None):
        """Calculate all HR metrics for the specified date range"""
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        current_date = start_date
        while current_date <= end_date:
            self.calculate_metrics_for_date(current_date)
            current_date += timedelta(days=1)
    
    def calculate_metrics_for_date(self, date):
        """Calculate metrics for a specific date"""
        # Headcount
        self._calculate_headcount(date)
        
        # Attrition rate (monthly)
        if date.day == 1:  # Calculate monthly on first day of month
            self._calculate_attrition_rate(date)
            self._calculate_new_hires(date)
            self._calculate_average_tenure(date)
            self._calculate_leave_utilization(date)
    
    def _calculate_headcount(self, date):
        """Calculate total headcount by department"""
        # Total headcount
        total_count = Employee.objects.filter(
            Q(hire_date__lte=date) &
            (Q(termination_date__isnull=True) | Q(termination_date__gt=date))
        ).count()
        
        HRMetric.objects.update_or_create(
            metric_type='headcount',
            date=date,
            department=None,
            defaults={
                'value': total_count,
                'month': date.month,
                'year': date.year,
                'quarter': (date.month - 1) // 3 + 1,
                'calculation_details': {'total_employees': total_count}
            }
        )
        
        # By department
        departments = Department.objects.all()
        for dept in departments:
            dept_count = Employee.objects.filter(
                Q(department=dept) &
                Q(hire_date__lte=date) &
                (Q(termination_date__isnull=True) | Q(termination_date__gt=date))
            ).count()
            
            HRMetric.objects.update_or_create(
                metric_type='headcount',
                date=date,
                department=dept,
                defaults={
                    'value': dept_count,
                    'month': date.month,
                    'year': date.year,
                    'quarter': (date.month - 1) // 3 + 1,
                    'calculation_details': {'department_employees': dept_count}
                }
            )
    
    def _calculate_attrition_rate(self, date):
        """Calculate monthly attrition rate"""
        # Get previous month date range
        if date.month == 1:
            prev_month = 12
            prev_year = date.year - 1
        else:
            prev_month = date.month - 1
            prev_year = date.year
        
        month_start = date.replace(month=prev_month, year=prev_year, day=1)
        if prev_month == 12:
            month_end = date.replace(month=1, year=prev_year + 1, day=1) - timedelta(days=1)
        else:
            month_end = date.replace(month=prev_month + 1, day=1) - timedelta(days=1)
        
        # Count terminations in the month
        terminations = Employee.objects.filter(
            termination_date__range=[month_start, month_end]
        ).count()
        
        # Average headcount during the month
        start_headcount = Employee.objects.filter(
            Q(hire_date__lt=month_start) &
            (Q(termination_date__isnull=True) | Q(termination_date__gte=month_start))
        ).count()
        
        end_headcount = Employee.objects.filter(
            Q(hire_date__lte=month_end) &
            (Q(termination_date__isnull=True) | Q(termination_date__gt=month_end))
        ).count()
        
        avg_headcount = (start_headcount + end_headcount) / 2 if (start_headcount + end_headcount) > 0 else 1
        attrition_rate = (terminations / avg_headcount) * 100
        
        HRMetric.objects.update_or_create(
            metric_type='attrition_rate',
            date=date,
            department=None,
            defaults={
                'value': terminations,
                'percentage_value': attrition_rate,
                'month': date.month,
                'year': date.year,
                'quarter': (date.month - 1) // 3 + 1,
                'calculation_details': {
                    'terminations': terminations,
                    'avg_headcount': avg_headcount,
                    'rate_percentage': attrition_rate
                }
            }
        )
    
    def _calculate_new_hires(self, date):
        """Calculate new hires for the previous month"""
        if date.month == 1:
            prev_month = 12
            prev_year = date.year - 1
        else:
            prev_month = date.month - 1
            prev_year = date.year
        
        month_start = date.replace(month=prev_month, year=prev_year, day=1)
        if prev_month == 12:
            month_end = date.replace(month=1, year=prev_year + 1, day=1) - timedelta(days=1)
        else:
            month_end = date.replace(month=prev_month + 1, day=1) - timedelta(days=1)
        
        new_hires = Employee.objects.filter(
            hire_date__range=[month_start, month_end]
        ).count()
        
        HRMetric.objects.update_or_create(
            metric_type='new_hires',
            date=date,
            department=None,
            defaults={
                'value': new_hires,
                'month': date.month,
                'year': date.year,
                'quarter': (date.month - 1) // 3 + 1,
                'calculation_details': {'new_hires_count': new_hires}
            }
        )
    
    def _calculate_average_tenure(self, date):
        """Calculate average employee tenure"""
        active_employees = Employee.objects.filter(
            Q(hire_date__lte=date) &
            (Q(termination_date__isnull=True) | Q(termination_date__gt=date))
        )
        
        if active_employees.exists():
            total_tenure_days = sum(
                (date - emp.hire_date).days for emp in active_employees
            )
            avg_tenure_days = total_tenure_days / active_employees.count()
            avg_tenure_years = avg_tenure_days / 365.25
        else:
            avg_tenure_years = 0
        
        HRMetric.objects.update_or_create(
            metric_type='average_tenure',
            date=date,
            department=None,
            defaults={
                'value': round(avg_tenure_years, 2),
                'month': date.month,
                'year': date.year,
                'quarter': (date.month - 1) // 3 + 1,
                'calculation_details': {
                    'average_tenure_years': avg_tenure_years,
                    'total_employees': active_employees.count()
                }
            }
        )
    
    def _calculate_leave_utilization(self, date):
        """Calculate leave utilization metrics"""
        # This assumes you have LeaveBalance and LeaveRequest models
        try:
            from leave.models import LeaveBalance, LeaveRequest
            
            # Get all active employees
            active_employees = Employee.objects.filter(
               Q(hire_date__lte=date) &
                (Q(termination_date__isnull=True) | Q(termination_date__gt=date))
            )
            
            total_allocated = 0
            total_used = 0
            
            for employee in active_employees:
                # Get leave balances for the employee
                balances = LeaveBalance.objects.filter(
                    employee=employee,
                    year=date.year
                )
                
                for balance in balances:
                    total_allocated += balance.total_days
                    total_used += balance.used_days
            
            utilization_rate = (total_used / total_allocated * 100) if total_allocated > 0 else 0
            
            HRMetric.objects.update_or_create(
                metric_type='leave_utilization',
                date=date,
                department=None,
                defaults={
                    'value': total_used,
                    'percentage_value': utilization_rate,
                    'month': date.month,
                    'year': date.year,
                    'quarter': (date.month - 1) // 3 + 1,
                    'calculation_details': {
                        'total_allocated': total_allocated,
                        'total_used': total_used,
                        'utilization_rate': utilization_rate
                    }
                }
            )
        except ImportError:
            # Leave models not available
            pass