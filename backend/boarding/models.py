from django.db import models
from django.contrib.auth import get_user_model
from employees.models import Employee, Department

User = get_user_model()

class ProcessTemplate(models.Model):
    PROCESS_TYPE_CHOICES = (
        ('onboarding', 'Onboarding'),
        ('offboarding', 'Offboarding'),
    )
    
    name = models.CharField(max_length=100)
    process_type = models.CharField(max_length=20, choices=PROCESS_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    departments = models.ManyToManyField(Department, related_name='process_templates', blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='created_process_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_process_type_display()})"


class TaskTemplate(models.Model):
    TASK_PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    process_template = models.ForeignKey(ProcessTemplate, on_delete=models.CASCADE, related_name='task_templates')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='department_tasks')
    assignee_role = models.CharField(max_length=100, blank=True, null=True, 
                                    help_text="Role description of the person who should complete this task")
    estimated_days = models.PositiveIntegerField(default=1, help_text="Estimated days to complete")
    priority = models.CharField(max_length=10, choices=TASK_PRIORITY_CHOICES, default='medium')
    is_mandatory = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order in which tasks should be completed")
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependent_tasks')
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name}"


class Process(models.Model):
    PROCESS_STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PROCESS_TYPE_CHOICES = (
        ('onboarding', 'Onboarding'),
        ('offboarding', 'Offboarding'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employee_processes')
    process_template = models.ForeignKey(ProcessTemplate, on_delete=models.SET_NULL, null=True, related_name='processes')
    process_type = models.CharField(max_length=20, choices=PROCESS_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=PROCESS_STATUS_CHOICES, default='planned')
    start_date = models.DateField()
    target_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='created_processes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Processes"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.get_process_type_display()} for {self.employee.full_name}"


class Task(models.Model):
    TASK_STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('pending_approval', 'Pending Approval'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    TASK_PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='process_tasks', null=True, blank=True)
    task_template = models.ForeignKey(TaskTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='task_departments')
    assignee = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='assigned_tasks', null=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='not_started')
    priority = models.CharField(max_length=10, choices=TASK_PRIORITY_CHOICES, default='medium')
    is_mandatory = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    completion_date = models.DateField(null=True, blank=True)
    completion_notes = models.TextField(blank=True, null=True)
    completed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_tasks')
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependent_tasks')
    
    class Meta:
        ordering = ['order', 'due_date']
    
    def __str__(self):
        return f"{self.name} - {self.assignee.full_name}"


class Equipment(models.Model):
    EQUIPMENT_TYPE_CHOICES = (
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('phone', 'Phone'),
        ('tablet', 'Tablet'),
        ('access_card', 'Access Card'),
        ('software_license', 'Software License'),
        ('other', 'Other'),
    )
    
    EQUIPMENT_STATUS_CHOICES = (
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
    )
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=EQUIPMENT_TYPE_CHOICES)
    identifier = models.CharField(max_length=100, unique=True, help_text="Serial number, asset tag, etc.")
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=EQUIPMENT_STATUS_CHOICES, default='available')
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.identifier})"


class EquipmentAssignment(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='equipment_assigned_to')
    assigned_date = models.DateField()
    expected_return_date = models.DateField(null=True, blank=True)
    actual_return_date = models.DateField(null=True, blank=True)
    condition_on_assignment = models.TextField(blank=True, null=True)
    condition_on_return = models.TextField(blank=True, null=True)
    assigned_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='equipment_assigned_by')
    received_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_returns')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.equipment.name} assigned to {self.employee.full_name}"
    
    def save(self, *args, **kwargs):
        # Update equipment status when assigned or returned
        if not self.pk:  # New assignment
            self.equipment.status = 'assigned'
            self.equipment.save()
        elif self.actual_return_date and not EquipmentAssignment.objects.get(pk=self.pk).actual_return_date:
            # Equipment returned
            self.equipment.status = 'available'
            self.equipment.save()
        
        super().save(*args, **kwargs)
