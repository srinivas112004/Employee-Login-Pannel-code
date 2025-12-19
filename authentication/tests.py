"""
Authentication App - Tests
Test cases for authentication functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class UserRegistrationTestCase(TestCase):
    """Test cases for user registration."""
    
    def setUp(self):
        self.client = APIClient()
        self.registration_url = '/api/auth/register/'
        
        self.valid_payload = {
            'email': 'test@company.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'employee',
            'employee_id': 'EMP001',
            'department': 'IT',
            'designation': 'Developer'
        }
    
    def test_valid_registration(self):
        """Test registration with valid data."""
        response = self.client.post(self.registration_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('tokens' in response.data)
        self.assertTrue(User.objects.filter(email='test@company.com').exists())
    
    def test_registration_with_mismatched_passwords(self):
        """Test registration with mismatched passwords."""
        payload = self.valid_payload.copy()
        payload['password2'] = 'DifferentPass123!'
        response = self.client.post(self.registration_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_with_duplicate_email(self):
        """Test registration with already existing email."""
        User.objects.create_user(
            email='test@company.com',
            password='TestPass123!',
            first_name='Existing',
            last_name='User'
        )
        response = self.client.post(self.registration_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(TestCase):
    """Test cases for user login."""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/auth/login/'
        
        self.user = User.objects.create_user(
            email='test@company.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            role='employee'
        )
    
    def test_valid_login(self):
        """Test login with valid credentials."""
        payload = {
            'email': 'test@company.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('tokens' in response.data)
        self.assertTrue('access' in response.data['tokens'])
        self.assertTrue('refresh' in response.data['tokens'])
    
    def test_invalid_password(self):
        """Test login with invalid password."""
        payload = {
            'email': 'test@company.com',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_email(self):
        """Test login with non-existent email."""
        payload = {
            'email': 'nonexistent@company.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
