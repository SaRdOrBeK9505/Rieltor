from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    LoginSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    UserCreateSerializer,
    ResetPasswordSerializer,
)
from .permissions import IsCompanyAdmin

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens.
    Uses LoginSerializer for validation.
    """
    serializer_class = LoginSerializer


class LoginView(generics.GenericAPIView):
    """
    API view for user login.
    Returns JWT access and refresh tokens along with user information.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import authenticate
        
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response(
                {'detail': 'Username yoki parol noto\'g\'ri'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'detail': 'Hisob faol emas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })


class RefreshTokenView(generics.GenericAPIView):
    """
    API view for refreshing JWT tokens.
    Uses the default TokenRefreshView from simplejwt.
    """
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer
        return TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        from rest_framework_simplejwt.views import TokenRefreshView
        view = TokenRefreshView.as_view()
        return view(request)


class ChangePasswordView(generics.GenericAPIView):
    """
    API view for changing user's own password.
    Requires old password for verification.
    """
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Parol muvaffaqiyatli o\'zgartirildi'})


class UserListView(generics.ListCreateAPIView):
    """
    API view for listing and creating users.
    Admin only.
    """
    serializer_class = UserSerializer
    permission_classes = [IsCompanyAdmin]

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting users.
    Admin only.
    """
    serializer_class = UserSerializer
    permission_classes = [IsCompanyAdmin]

    def get_queryset(self):
        return User.objects.all()


class ResetUserPasswordView(generics.GenericAPIView):
    """
    API view for resetting user password (admin only).
    Allows admins to reset any user's password.
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsCompanyAdmin]

    def post(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(
            data=request.data,
            context={'user': user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Parol muvaffaqiyatli o\'zgartirildi'})
