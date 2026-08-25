from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Returns JWT access and refresh tokens along with user information.
    """
    username = serializers.CharField(
        help_text="Username of the user"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="User password"
    )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user's own password.
    Requires old password for verification.
    """
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Current password for verification"
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text="New password (minimum 8 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Parollar mos kelmaydi")
        if len(data['new_password']) < 8:
            raise serializers.ValidationError("Parol kamida 8 ta belgidan iborat bo'lishi kerak")
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details.
    Used for listing and retrieving user information.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone_number', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    Password is write-only and must be at least 8 characters.
    Default role is 'operator'.
    """
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text="User password (minimum 8 characters)"
    )
    role = serializers.ChoiceField(
        choices=[('admin', 'Admin'), ('operator', 'Operator')],
        default='operator',
        required=False,
        help_text="User role (default: operator)"
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role', 'phone_number']

    def create(self, validated_data):
        password = validated_data.pop('password')
        # Set default role to operator if not provided
        if 'role' not in validated_data:
            validated_data['role'] = 'operator'
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer for resetting user password (admin only).
    Allows admins to reset any user's password.
    """
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text="New password for the user (minimum 8 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Parollar mos kelmaydi")
        if len(data['new_password']) < 8:
            raise serializers.ValidationError("Parol kamida 8 ta belgidan iborat bo'lishi kerak")
        return data

    def save(self):
        user = self.context['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
