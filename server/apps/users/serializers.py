"""
Serializers for the users app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import School

User = get_user_model()


class SchoolSerializer(serializers.ModelSerializer):
    """
    Serializer for School model.
    """
    class Meta:
        model = School
        fields = ["id", "name", "identifier", "region", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    """
    Base serializer for User model.
    """
    school = SchoolSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "school",
            "subject",
            "is_active",
            "is_verified",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_verified"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    """
    password = serializers.CharField(write_only=True, min_length=12)
    school_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "school_id",
            "subject",
        ]
    
    def validate_role(self, value):
        """Validate that the role is valid."""
        valid_roles = ["admin", "teacher", "student"]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}")
        return value
    
    def create(self, validated_data):
        school_id = validated_data.pop("school_id", None)
        password = validated_data.pop("password")
        
        if school_id:
            validated_data["school_id"] = school_id
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating users.
    """
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "subject",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    """
    school = SchoolSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "school",
            "subject",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "date_joined"]


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer for token response.
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default="Bearer")
    expires_in = serializers.IntegerField()
    user = UserSerializer()


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)
    confirm_password = serializers.CharField(write_only=True, min_length=12)
    
    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("New passwords do not match.")
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=12)
    confirm_password = serializers.CharField(write_only=True, min_length=12)
    
    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data
