from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from employees.models import Employee
import uuid

class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    max_days_per_year = models.PositiveIntegerField(default=0)  # 0 means unlimited
    color_code = models.CharField(max_length=7, default="#3498db")  # Hex color code
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class LeavePolicy(models.Model):
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='policies')
    department = models.ForeignKey('employees.Department', on_delete=models.CASCADE, null=True, blank=True)
    designation = models.ForeignKey('employees.Designation', on_delete=models.CASCADE, null=True, blank=True)
    days_allowed = models.PositiveIntegerField()
    accrual_period = models.CharField(max_length=20, default='yearly')  # yearly, monthly, quarterly
    carries_forward = models.BooleanField(default=False)
    max_carry_forward_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.department and self.designation:
            return f"{self.leave_type.name} - {self.department.name} - {self.designation.title}"
        elif self.department:
            return f"{self.leave_type.name} - {self.department.name} - All Designations"
        elif self.designation:
            return f"{self.leave_type.name} - All Departments - {self.designation.title}"
        else:
            return f"{self.leave_type.name} - All Departments and Designations"

    class Meta:
        unique_together = ('leave_type', 'department', 'designation')

class LeaveBalance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    total_days = models.PositiveIntegerField()
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    pending_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    carried_forward_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} - {self.year}"

    @property
    def available_days(self):
        return self.total_days - self.used_days - self.pending_days

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

class LeaveRequest(models.Model):
    LEAVE_REQUEST_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    half_day = models.BooleanField(default=False)
    half_day_type = models.CharField(max_length=10, choices=[('FIRST', 'First Half'), ('SECOND', 'Second Half')], null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=LEAVE_REQUEST_STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} - {self.start_date} to {self.end_date}"

    @property
    def number_of_days(self):
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            if self.half_day:
                return delta - 0.5
            return delta
        return 0

    def clean(self):
        # Check if end_date is not before start_date
        if self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date')

        # Check if half_day_type is provided when half_day is True
        if self.half_day and not self.half_day_type:
            raise ValidationError('Half day type must be specified when half day is selected')

    def save(self, *args, **kwargs):
        self.clean()
        
        # Handle status changes
        if self._state.adding:  # New leave request
            pass  # No special handling needed for new requests
        else:
            old_instance = LeaveRequest.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                if self.status == 'APPROVED':
                    self.approved_at = timezone.now()
                    # Update leave balance in a transaction
                    from django.db import transaction
                    with transaction.atomic():
                        year = self.start_date.year
                        balance, created = LeaveBalance.objects.get_or_create(
                            employee=self.employee,
                            leave_type=self.leave_type,
                            year=year,
                            defaults={'total_days': 0}
                        )
                        if old_instance.status == 'PENDING':
                            balance.pending_days -= self.number_of_days
                            balance.used_days += self.number_of_days
                        balance.save()
                elif self.status == 'REJECTED' or self.status == 'CANCELLED':
                    if old_instance.status == 'PENDING':
                        # Update leave balance to remove pending days
                        from django.db import transaction
                        with transaction.atomic():
                            year = self.start_date.year
                            balance = LeaveBalance.objects.get(
                                employee=self.employee,
                                leave_type=self.leave_type,
                                year=year
                            )
                            balance.pending_days -= self.number_of_days
                            balance.save()
                    elif old_instance.status == 'APPROVED':
                        # Update leave balance to remove used days
                        from django.db import transaction
                        with transaction.atomic():
                            year = self.start_date.year
                            balance = LeaveBalance.objects.get(
                                employee=self.employee,
                                leave_type=self.leave_type,
                                year=year
                            )
                            balance.used_days -= self.number_of_days
                            balance.save()
        
        super().save(*args, **kwargs)
        
        # If this is a new pending request, update leave balance
        if self._state.adding and self.status == 'PENDING':
            from django.db import transaction
            with transaction.atomic():
                year = self.start_date.year
                balance, created = LeaveBalance.objects.get_or_create(
                    employee=self.employee,
                    leave_type=self.leave_type,
                    year=year,
                    defaults={'total_days': 0}
                )
                balance.pending_days += self.number_of_days
                balance.save()

class LeaveComment(models.Model):
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='comments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.leave_request} by {self.employee.full_name}"

    class Meta:
        ordering = ['-created_at']

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)  # True for holidays that occur on the same date every year
    applicable_departments = models.ManyToManyField('employees.Department', blank=True, related_name='holidays')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.date}"

    class Meta:
        ordering = ['date']