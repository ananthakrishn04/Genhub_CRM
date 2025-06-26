from django.shortcuts import render

# Create your views here.
# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from .serializers import (
    UserSerializer,
    PermissionSerializer,
    ModelPermissionAssignmentSerializer,
    UserLoginSerializer
)

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import permissions
from employees.models import Employee

class UserPermissionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def assign_model_permissions(self, request):
        """
        Assign CRUD permissions for a specific model to a user
        """
        serializer = ModelPermissionAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        try:
            user = User.objects.get(id=data['user_id'])
            model = apps.get_model(data['app_label'], data['model_name'])
            content_type = ContentType.objects.get_for_model(model)
            
            # Permission codenames follow Django's convention
            permission_codenames = [
                f"{perm}_{data['model_name'].lower()}" for perm in data['permissions']
            ]
            
            # Get permission objects
            perms = Permission.objects.filter(
                content_type=content_type,
                codename__in=permission_codenames
            )
            
            # Assign permissions to user
            user.user_permissions.add(*perms)
            
            return Response({
                'message': f'Permissions assigned successfully to {user.username}',
                'permissions': PermissionSerializer(perms, many=True).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def revoke_model_permissions(self, request):
        """
        Revoke CRUD permissions for a specific model from a user
        """
        serializer = ModelPermissionAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        try:
            user = Employee.objects.get(id=data['user_id']).user
            model = apps.get_model(data['app_label'], data['model_name'])
            content_type = ContentType.objects.get_for_model(model)
            
            # Permission codenames follow Django's convention
            permission_codenames = [
                f"{perm}_{data['model_name'].lower()}" for perm in data['permissions']
            ]
            
            # Get permission objects
            perms = Permission.objects.filter(
                content_type=content_type,
                codename__in=permission_codenames
            )
            
            # Revoke permissions from user
            user.user_permissions.remove(*perms)
            
            return Response({
                'message': f'Permissions revoked successfully from {user.username}',
                'permissions': PermissionSerializer(perms, many=True).data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class AdminLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data

        if user is not None:
            try:
                employee = user.employee_profile
                employee_id = str(employee.employee_id)

            except Exception:
                employee_id = None

            refresh = RefreshToken.for_user(user)
            # Determine role
            if user.is_superuser:
                role = 'admin'
            elif user.is_staff:
                role = 'staff'
            elif user.groups.exists():
                role = user.groups.first().name
            else:
                role = 'employee'
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'employee_id': employee_id,
                'role': role,
            })
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)