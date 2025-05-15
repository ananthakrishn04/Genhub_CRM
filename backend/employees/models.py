from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    parent_department = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_departments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Designation(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.department.name})"
    
    class Meta:
        ordering = ['title']

class Employee(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    MARITAL_STATUS_CHOICES = (
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    )
    
    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    # employee_id = models.CharField(max_length=20, unique=True)
    employee_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='employee_profiles/', null=True, blank=True)
    
    # Contact Information
    phone = models.CharField(max_length=20, null=True, blank=True)
    alternative_phone = models.CharField(max_length=20, null=True, blank=True)
    present_address = models.TextField(null=True, blank=True)
    permanent_address = models.TextField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Personal Information
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    blood_group = models.CharField(max_length=5, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    
    # Employment Information
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, related_name='employees')
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='team_members')
    date_of_joining = models.DateField()
    employment_status = models.CharField(max_length=20, default='Active')  # Active, Probation, Terminated, etc.
    employment_type = models.CharField(max_length=20, default='Full-time')  # Full-time, Part-time, Contract, etc.
    
    # Other Information
    skills = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    
    # System Fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    class Meta:
        ordering = ['first_name', 'last_name']
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class EmployeeEducation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    grade = models.CharField(max_length=20, null=True, blank=True)
    activities = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.degree} from {self.institution}"
    
    class Meta:
        ordering = ['-end_date', '-start_date']

class EmployeeExperience(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=200)
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.title} at {self.company}"
    
    class Meta:
        ordering = ['-end_date', '-start_date']

class EmployeeSkill(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='skill_list')
    skill = models.CharField(max_length=100)
    proficiency_level = models.PositiveSmallIntegerField(default=1)  # 1-5 scale
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.skill}"
    
    class Meta:
        unique_together = ('employee', 'skill')
        ordering = ['-proficiency_level', 'skill']

class EmployeeTimeline(models.Model):
    EVENT_TYPES = (
        ('JOIN', 'Joined'),
        ('PROM', 'Promotion'),
        ('TRAN', 'Transfer'),
        ('APPR', 'Appraisal'),
        ('AWAR', 'Award'),
        ('CERT', 'Certification'),
        ('TERM', 'Termination'),
        ('OTH', 'Other'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='timeline')
    event_type = models.CharField(max_length=4, choices=EVENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    event_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_timeline_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.title} on {self.event_date}"
    
    class Meta:
        ordering = ['-event_date']