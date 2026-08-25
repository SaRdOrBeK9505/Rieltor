from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserPermissionsTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            role="admin"
        )

        self.operator = User.objects.create_user(
            username="operator",
            password="testpass123",
            role="operator"
        )

        # Create API clients
        self.admin_client = APIClient()
        self.operator_client = APIClient()

        # Authenticate clients
        admin_token = RefreshToken.for_user(self.admin)
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token.access_token}')

        operator_token = RefreshToken.for_user(self.operator)
        self.operator_client.credentials(HTTP_AUTHORIZATION=f'Bearer {operator_token.access_token}')

    def test_admin_can_create_user(self):
        response = self.admin_client.post('/api/auth/users/', {
            'username': 'newuser',
            'password': 'testpass123',
            'role': 'operator',
            'phone_number': '+998901234567'
        })
        self.assertEqual(response.status_code, 201)

    def test_operator_cannot_create_user(self):
        response = self.operator_client.post('/api/auth/users/', {
            'username': 'newuser',
            'password': 'testpass123',
            'role': 'operator',
            'phone_number': '+998901234567'
        })
        self.assertEqual(response.status_code, 403)

    def test_operator_cannot_see_users_list(self):
        response = self.operator_client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 403)

    def test_both_can_change_own_password(self):
        # Admin changes password
        response = self.admin_client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, 200)

        # Operator changes password
        response = self.operator_client.post('/api/auth/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, 200)
