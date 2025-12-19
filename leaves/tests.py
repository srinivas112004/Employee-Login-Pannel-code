from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
from .models import Leave, LeaveType, LeaveBalance

User = get_user_model()


class LeaveModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='employee'
        )
        self.leave_type = LeaveType.objects.create(
            name='Casual Leave',
            code='CL',
            default_days=12
        )

    def test_leave_creation(self):
        leave = Leave.objects.create(
            user=self.user,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            reason='Personal work'
        )
        self.assertEqual(leave.status, 'pending')
        self.assertIsNotNone(leave.total_days)

    def test_calculate_leave_days(self):
        # Monday to Wednesday (3 working days)
        leave = Leave(
            user=self.user,
            leave_type=self.leave_type,
            start_date=date(2025, 11, 3),  # Monday
            end_date=date(2025, 11, 5),    # Wednesday
            reason='Test'
        )
        days = leave.calculate_leave_days()
        self.assertEqual(days, 3)


class LeaveAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.employee = User.objects.create_user(
            email='employee@example.com',
            password='testpass123',
            role='employee',
            first_name='John',
            last_name='Doe'
        )
        
        self.manager = User.objects.create_user(
            email='manager@example.com',
            password='testpass123',
            role='manager',
            first_name='Jane',
            last_name='Manager'
        )
        
        # Create leave type
        self.leave_type = LeaveType.objects.create(
            name='Casual Leave',
            code='CL',
            default_days=12
        )
        
        # Create leave balance
        self.balance = LeaveBalance.objects.create(
            user=self.employee,
            leave_type=self.leave_type,
            year=date.today().year,
            total_days=12,
            used_days=0,
            available_days=12
        )

    def test_apply_leave_success(self):
        self.client.force_authenticate(user=self.employee)
        
        data = {
            'leave_type': self.leave_type.id,
            'start_date': (date.today() + timedelta(days=5)).isoformat(),
            'end_date': (date.today() + timedelta(days=7)).isoformat(),
            'reason': 'Personal work'
        }
        
        response = self.client.post('/api/leaves/leaves/apply/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Leave.objects.count(), 1)

    def test_apply_leave_past_date(self):
        self.client.force_authenticate(user=self.employee)
        
        data = {
            'leave_type': self.leave_type.id,
            'start_date': (date.today() - timedelta(days=1)).isoformat(),
            'end_date': date.today().isoformat(),
            'reason': 'Personal work'
        }
        
        response = self.client.post('/api/leaves/leaves/apply/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_leave_balance(self):
        self.client.force_authenticate(user=self.employee)
        
        response = self.client.get('/api/leaves/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(float(response.data[0]['available_days']), 12.0)

    def test_get_leave_history(self):
        self.client.force_authenticate(user=self.employee)
        
        # Create a leave
        Leave.objects.create(
            user=self.employee,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            total_days=3,
            reason='Test leave'
        )
        
        response = self.client.get('/api/leaves/leaves/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_leave_types(self):
        self.client.force_authenticate(user=self.employee)
        
        response = self.client.get('/api/leaves/types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_access(self):
        response = self.client.get('/api/leaves/balance/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
