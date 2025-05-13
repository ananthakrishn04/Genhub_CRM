from django.db import models
from django.contrib.auth import get_user_model
from employees.models import Employee  # Import Employee model from your existing app
from django.utils import timezone

User = get_user_model()

class DocumentCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Document Categories"


class Template(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='templates')
    content = models.TextField(help_text="HTML content with placeholders for variables")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Document(models.Model):
    DOCUMENT_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_signature', 'Pending Signature'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('archived', 'Archived'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='documents')
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_documents')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/%Y/%m/')
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='draft')
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    signature_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    class Meta:
        ordering = ['-created_at']


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to='document_versions/%Y/%m/')
    changes = models.TextField(blank=True, null=True, help_text="Description of changes in this version")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='document_versions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('document', 'version_number')
        ordering = ['-version_number']
    
    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"


class DocumentSignature(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signatures')
    signer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signed_documents')
    signature_image = models.FileField(upload_to='signatures/%Y/%m/', null=True, blank=True)
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Signature by {self.signer.username} on {self.document.title}"