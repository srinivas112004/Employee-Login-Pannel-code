"""
Day 4: Management command to create sample dashboard data for testing.
Usage: python manage.py create_dashboard_sample_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import User
from dashboard.models import Announcement, Task, LeaveBalance


class Command(BaseCommand):
    help = 'Creates sample data for Day 4 Dashboard APIs testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating Day 4 sample data...\n'))

        # Get or create admin and regular users
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: {admin_user.email}'))
        else:
            self.stdout.write(f'  Admin user already exists: {admin_user.email}')

        employee_user, created = User.objects.get_or_create(
            email='employee@example.com',
            defaults={
                'role': 'employee',
                'is_email_verified': True
            }
        )
        if created:
            employee_user.set_password('employee123')
            employee_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created employee user: {employee_user.email}'))
        else:
            self.stdout.write(f'  Employee user already exists: {employee_user.email}')

        manager_user, created = User.objects.get_or_create(
            email='manager@example.com',
            defaults={
                'role': 'manager',
                'is_email_verified': True
            }
        )
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created manager user: {manager_user.email}'))
        else:
            self.stdout.write(f'  Manager user already exists: {manager_user.email}')

        self.stdout.write('\n--- Creating Announcements ---')
        
        # Create announcements
        announcements_data = [
            {
                'title': 'Company Holiday - New Year 2026',
                'content': 'Office will be closed on January 1st, 2026 for New Year celebrations.',
                'priority': 'high',
                'created_by': admin_user,
                'expires_at': timezone.now() + timedelta(days=30)
            },
            {
                'title': 'New Project Launch',
                'content': 'We are excited to announce the launch of Project Phoenix next month.',
                'priority': 'medium',
                'created_by': manager_user,
                'expires_at': timezone.now() + timedelta(days=15)
            },
            {
                'title': 'Team Building Event',
                'content': 'Join us for a team building event this Friday at 4 PM.',
                'priority': 'low',
                'created_by': manager_user,
                'expires_at': timezone.now() + timedelta(days=5)
            },
            {
                'title': 'URGENT: Security Update Required',
                'content': 'Please update your passwords and enable 2FA by end of day.',
                'priority': 'urgent',
                'created_by': admin_user,
                'expires_at': timezone.now() + timedelta(days=1)
            }
        ]

        for ann_data in announcements_data:
            announcement, created = Announcement.objects.get_or_create(
                title=ann_data['title'],
                defaults=ann_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created announcement: {announcement.title}'))
            else:
                self.stdout.write(f'  Announcement already exists: {announcement.title}')

        self.stdout.write('\n--- Creating Tasks ---')

        # Create tasks
        tasks_data = [
            {
                'title': 'Complete Project Documentation',
                'description': 'Write comprehensive documentation for the Employee Management System.',
                'status': 'todo',
                'priority': 'high',
                'assigned_to': employee_user,
                'assigned_by': manager_user,
                'due_date': timezone.now() + timedelta(days=7)
            },
            {
                'title': 'Code Review - Authentication Module',
                'description': 'Review and provide feedback on the authentication module code.',
                'status': 'in_progress',
                'priority': 'medium',
                'assigned_to': employee_user,
                'assigned_by': manager_user,
                'due_date': timezone.now() + timedelta(days=3)
            },
            {
                'title': 'Fix Dashboard UI Bugs',
                'description': 'Fix responsive layout issues in the dashboard.',
                'status': 'review',
                'priority': 'medium',
                'assigned_to': employee_user,
                'assigned_by': manager_user,
                'due_date': timezone.now() + timedelta(days=2)
            },
            {
                'title': 'Deploy to Production',
                'description': 'Deploy the latest version to production server.',
                'status': 'completed',
                'priority': 'urgent',
                'assigned_to': employee_user,
                'assigned_by': admin_user,
                'due_date': timezone.now() - timedelta(days=2),
                'completed_at': timezone.now() - timedelta(days=1)
            },
            {
                'title': 'Update Dependencies',
                'description': 'Update all package dependencies to latest versions.',
                'status': 'todo',
                'priority': 'low',
                'assigned_to': employee_user,
                'assigned_by': admin_user,
                'due_date': timezone.now() + timedelta(days=14)
            },
            {
                'title': 'OVERDUE: Write API Tests',
                'description': 'Write unit tests for all API endpoints.',
                'status': 'todo',
                'priority': 'urgent',
                'assigned_to': employee_user,
                'assigned_by': manager_user,
                'due_date': timezone.now() - timedelta(days=3)  # Overdue
            }
        ]

        for task_data in tasks_data:
            task, created = Task.objects.get_or_create(
                title=task_data['title'],
                defaults=task_data
            )
            if created:
                status_symbol = '✓' if task_data['status'] == 'completed' else '⏳'
                self.stdout.write(self.style.SUCCESS(f'{status_symbol} Created task: {task.title}'))
            else:
                self.stdout.write(f'  Task already exists: {task.title}')

        self.stdout.write('\n--- Creating Leave Balances ---')

        # Create leave balances for employee
        current_year = timezone.now().year
        leave_balances_data = [
            {
                'user': employee_user,
                'leave_type': 'annual',
                'total_days': 20,
                'used_days': 5,
                'year': current_year
            },
            {
                'user': employee_user,
                'leave_type': 'sick',
                'total_days': 10,
                'used_days': 2,
                'year': current_year
            },
            {
                'user': employee_user,
                'leave_type': 'casual',
                'total_days': 5,
                'used_days': 1,
                'year': current_year
            },
            {
                'user': manager_user,
                'leave_type': 'annual',
                'total_days': 25,
                'used_days': 10,
                'year': current_year
            },
            {
                'user': manager_user,
                'leave_type': 'sick',
                'total_days': 12,
                'used_days': 3,
                'year': current_year
            }
        ]

        for lb_data in leave_balances_data:
            leave_balance, created = LeaveBalance.objects.get_or_create(
                user=lb_data['user'],
                leave_type=lb_data['leave_type'],
                year=lb_data['year'],
                defaults=lb_data
            )
            if created:
                remaining = leave_balance.remaining_days
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Created leave balance: {leave_balance.user.email} - '
                    f'{leave_balance.get_leave_type_display()} ({remaining} days remaining)'
                ))
            else:
                self.stdout.write(
                    f'  Leave balance already exists: {leave_balance.user.email} - '
                    f'{leave_balance.get_leave_type_display()}'
                )

        self.stdout.write('\n' + self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Day 4 sample data creation complete!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('\n📋 Summary:')
        self.stdout.write(f'  • Users: {User.objects.count()}')
        self.stdout.write(f'  • Announcements: {Announcement.objects.count()}')
        self.stdout.write(f'  • Tasks: {Task.objects.count()}')
        self.stdout.write(f'  • Leave Balances: {LeaveBalance.objects.count()}')
        self.stdout.write('\n🔐 Test Credentials:')
        self.stdout.write('  • Admin: admin@example.com / admin123')
        self.stdout.write('  • Manager: manager@example.com / manager123')
        self.stdout.write('  • Employee: employee@example.com / employee123')
        self.stdout.write('\n✅ You can now test Day 4 APIs in Postman!')
