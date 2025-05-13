from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import DocumentCategory, Template, Document, DocumentVersion, DocumentSignature
from .serializers import (
    DocumentCategorySerializer, TemplateSerializer, 
    DocumentListSerializer, DocumentDetailSerializer,
    DocumentVersionSerializer, DocumentSignatureSerializer
)


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'status', 'employee', 'is_signed']
    search_fields = ['title', 'description', 'tags']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        return DocumentDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        document = self.get_object()
        # Here you would implement PDF generation logic using WeasyPrint/ReportLab
        # This is a placeholder for the actual implementation
        return Response({"message": "PDF generation initiated"}, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def request_signature(self, request, pk=None):
        document = self.get_object()
        # Update document status
        document.status = 'pending_signature'
        document.save()
        # Here you would implement e-signature request logic
        # This is a placeholder for the actual implementation with DocuSign/HelloSign
        return Response({"message": "Signature request sent"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def mark_signed(self, request, pk=None):
        document = self.get_object()
        document.is_signed = True
        document.signature_date = timezone.now()
        document.status = 'active'
        document.save()
        
        # Create signature record
        DocumentSignature.objects.create(
            document=document,
            signer=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({"message": "Document marked as signed"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        document = self.get_object()
        
        # Get the latest version number and increment
        latest_version = document.versions.order_by('-version_number').first()
        new_version_number = 1 if not latest_version else latest_version.version_number + 1
        
        # Create new version
        serializer = DocumentVersionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                document=document,
                version_number=new_version_number,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['document']


class DocumentSignatureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentSignature.objects.all()
    serializer_class = DocumentSignatureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['document', 'signer', 'is_valid']