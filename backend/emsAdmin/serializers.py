from rest_framework import serializers
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

class ModelPermissionAssignmentSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    app_label = serializers.CharField()
    model_name = serializers.CharField()
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=['add', 'change', 'delete', 'view']),
        min_length=1
    )

    def validate(self, data):
        """
        Validate that the user exists and the model exists in the specified app
        """
        try:
            User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        
        return data

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        return user