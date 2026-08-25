from django.urls import path
from .views import (
    LoginView,
    RefreshTokenView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    ResetUserPasswordView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/reset-password/', ResetUserPasswordView.as_view(), name='reset-user-password'),
]
