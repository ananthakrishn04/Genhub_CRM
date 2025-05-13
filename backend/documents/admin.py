from django.contrib import admin
from .models import DocumentCategory, Template, Document, DocumentVersion, DocumentSignature


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_by', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ('created_at', 'created_by')


class DocumentSignatureInline(admin.TabularInline):
    model = DocumentSignature
    extra = 0
    readonly_fields = ('signed_at', 'ip_address')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'employee', 'category', 'status', 'issue_date', 'expiry_date', 'is_signed')
    list_filter = ('status', 'category', 'is_signed', 'issue_date', 'expiry_date')
    search_fields = ('title', 'description', 'employee__first_name', 'employee__last_name', 'tags')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DocumentVersionInline, DocumentSignatureInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'employee', 'category', 'template')
        }),
        ('Document Details', {
            'fields': ('file', 'tags', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date', 'created_at', 'updated_at')
        }),
        ('Signature Information', {
            'fields': ('is_signed', 'signature_date')
        }),
    )


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('document__title', 'changes')
    readonly_fields = ('created_at',)


@admin.register(DocumentSignature)
class DocumentSignatureAdmin(admin.ModelAdmin):
    list_display = ('document', 'signer', 'signed_at', 'is_valid', 'ip_address')
    list_filter = ('signed_at', 'is_valid')
    search_fields = ('document__title', 'signer__username', 'signer__first_name', 'signer__last_name')
    readonly_fields = ('signed_at', 'ip_address')