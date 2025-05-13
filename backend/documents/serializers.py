from rest_framework import serializers
from .models import DocumentCategory, Template, Document, DocumentVersion, DocumentSignature


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = '__all__'


class TemplateSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = Template
        fields = '__all__'


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = DocumentVersion
        fields = '__all__'


class DocumentSignatureSerializer(serializers.ModelSerializer):
    signer_name = serializers.ReadOnlyField(source='signer.get_full_name')
    
    class Meta:
        model = DocumentSignature
        fields = '__all__'


class DocumentListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    employee_name = serializers.ReadOnlyField(source='employee.full_name')
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'category', 'category_name', 
            'employee', 'employee_name', 'status',
            'issue_date', 'expiry_date', 'is_signed', 'created_at'
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    employee_name = serializers.ReadOnlyField(source='employee.full_name')
    template_name = serializers.ReadOnlyField(source='template.name', allow_null=True)
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    versions = DocumentVersionSerializer(many=True, read_only=True)
    signatures = DocumentSignatureSerializer(many=True, read_only=True)
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = '__all__'
    
    def get_tags_list(self, obj):
        return [tag.strip() for tag in obj.tags.split(',')] if obj.tags else []