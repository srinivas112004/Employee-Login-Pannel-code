"""
Management command to create sample data for Day 6 Project Management features.
Creates projects, milestones, subtasks, and file attachments.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from authentication.models import User
from dashboard.models import Project, Milestone, Task, FileAttachment
from django.core.files.base import ContentFile
import io


class Command(BaseCommand):
    help = 'Create sample data for Day 6 Project Management features'

    def add_arguments(self, parser):
        parser.add_argument(
            '--projects',
            type=int,
            default=3,
            help='Number of projects to create (default: 3)'
        )

    def handle(self, *args, **options):
        num_projects = options['projects']
        
        self.stdout.write(self.style.WARNING(f'\nCreating {num_projects} sample projects with Day 6 features...'))
        
        # Get users
        admin = User.objects.filter(role='admin').first()
        manager = User.objects.filter(role='manager').first()
        employees = list(User.objects.filter(role='employee')[:5])
        
        if not admin:
            self.stdout.write(self.style.ERROR('\n❌ No admin user found!'))
            self.stdout.write('Please create an admin user first.')
            return
        
        if not employees:
            self.stdout.write(self.style.ERROR('\n❌ No employee users found!'))
            self.stdout.write('Please create employee users first.')
            return
        
        project_manager = manager if manager else admin
        self.stdout.write(f'\n✅ Found {len(employees)} employees')
        
        # Sample project data
        project_templates = [
            {
                'name': 'Employee Management System',
                'description': 'Build a comprehensive employee management system with authentication, task management, and reporting features.',
                'status': 'active',
                'milestones': [
                    {'name': 'Authentication Module', 'description': 'Complete user authentication with 2FA'},
                    {'name': 'Dashboard Implementation', 'description': 'Build employee dashboard'},
                    {'name': 'Task Management', 'description': 'Implement task creation and assignment'},
                ]
            },
            {
                'name': 'Mobile App Development',
                'description': 'Develop iOS and Android apps for the employee portal with offline capabilities.',
                'status': 'planning',
                'milestones': [
                    {'name': 'UI/UX Design', 'description': 'Design mockups and wireframes'},
                    {'name': 'API Integration', 'description': 'Connect mobile apps to backend APIs'},
                    {'name': 'Testing & QA', 'description': 'Comprehensive testing on both platforms'},
                ]
            },
            {
                'name': 'Data Migration Project',
                'description': 'Migrate legacy employee data to new system with data validation and cleanup.',
                'status': 'completed',
                'milestones': [
                    {'name': 'Data Analysis', 'description': 'Analyze legacy data structure'},
                    {'name': 'Migration Scripts', 'description': 'Write automated migration scripts'},
                    {'name': 'Validation', 'description': 'Validate migrated data'},
                ]
            },
        ]
        
        created_projects = []
        
        # Create projects
        for i in range(num_projects):
            template = project_templates[i % len(project_templates)]
            
            start_date = date.today() - timedelta(days=30 * i)
            deadline = start_date + timedelta(days=90)
            
            project = Project.objects.create(
                name=f"{template['name']} (Project {i+1})",
                description=template['description'],
                status=template['status'],
                manager=project_manager,
                created_by=admin,
                start_date=start_date,
                deadline=deadline
            )
            created_projects.append(project)
            
            # Create milestones for project
            for j, milestone_data in enumerate(template['milestones']):
                due_date = project.start_date + timedelta(days=30 * (j + 1))
                
                # Set milestone status based on project status and due date
                if project.status == 'completed':
                    m_status = 'completed'
                elif due_date < date.today():
                    m_status = 'completed' if j == 0 else 'in_progress'
                else:
                    m_status = 'pending'
                
                Milestone.objects.create(
                    project=project,
                    name=milestone_data['name'],
                    description=milestone_data['description'],
                    status=m_status,
                    due_date=due_date
                )
            
            # Create tasks for project
            task_titles = [
                'Set up development environment',
                'Design database schema',
                'Implement user authentication',
                'Build REST API endpoints',
                'Create frontend UI components',
                'Write unit tests',
                'Perform code review',
                'Deploy to staging',
            ]
            
            for j in range(min(6, len(task_titles))):
                employee = employees[j % len(employees)]
                
                task_status = 'completed' if project.status == 'completed' else \
                             ['todo', 'in_progress', 'review', 'completed'][j % 4]
                
                parent_task = Task.objects.create(
                    title=f"{task_titles[j]} - {project.name}",
                    description=f"Complete {task_titles[j].lower()} for the project",
                    status=task_status,
                    priority=['low', 'medium', 'high', 'urgent'][j % 4],
                    assigned_to=employee,
                    assigned_by=project_manager,
                    project=project,
                    due_date=project.deadline - timedelta(days=10 * (6 - j))
                )
                
                # Create subtasks for first 2 tasks
                if j < 2:
                    subtask_titles = [
                        f'Subtask 1: Research and planning',
                        f'Subtask 2: Implementation',
                        f'Subtask 3: Testing',
                    ]
                    
                    for k, subtask_title in enumerate(subtask_titles):
                        Task.objects.create(
                            title=f"{parent_task.title} - {subtask_title}",
                            description=f"Subtask for {parent_task.title}",
                            status='completed' if k == 0 else 'in_progress',
                            priority=parent_task.priority,
                            assigned_to=employee,
                            assigned_by=project_manager,
                            project=project,
                            parent_task=parent_task,
                            due_date=parent_task.due_date - timedelta(days=3 - k)
                        )
            
            # Create sample file attachments (simulate files)
            attachment_names = [
                ('Project_Requirements.pdf', 'pdf', 1024 * 500),  # 500KB
                ('Design_Mockups.png', 'png', 1024 * 1024 * 2),  # 2MB
                ('Sprint_Plan.xlsx', 'xlsx', 1024 * 200),  # 200KB
            ]
            
            for name, file_type, size in attachment_names:
                # Create a simple text file as placeholder
                content = f"Sample attachment for {project.name}".encode()
                file_content = ContentFile(content, name=name)
                
                FileAttachment.objects.create(
                    project=project,
                    file=file_content,
                    file_name=name,
                    file_type=file_type,
                    file_size=size,
                    uploaded_by=admin
                )
            
            self.stdout.write(f'  ✅ Created project {project.id}: {project.name[:50]}...')
        
        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n✅ Sample data created successfully!\n'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'  • Projects created: {len(created_projects)}')
        self.stdout.write(f'  • Total milestones: {Milestone.objects.count()}')
        self.stdout.write(f'  • Total tasks (including subtasks): {Task.objects.count()}')
        self.stdout.write(f'  • Parent tasks: {Task.objects.filter(parent_task__isnull=True).count()}')
        self.stdout.write(f'  • Subtasks: {Task.objects.filter(parent_task__isnull=False).count()}')
        self.stdout.write(f'  • Total attachments: {FileAttachment.objects.count()}')
        
        self.stdout.write(f'\n📝 Project IDs created: {[p.id for p in created_projects]}')
        
        self.stdout.write(f'\n🧪 Test these projects in Postman:')
        self.stdout.write(f'  GET /api/dashboard/projects/')
        self.stdout.write(f'  GET /api/dashboard/projects/{created_projects[0].id}/')
        self.stdout.write(f'  GET /api/dashboard/projects/{created_projects[0].id}/milestones/')
        self.stdout.write(f'  GET /api/dashboard/tasks/?project={created_projects[0].id}')
        
        self.stdout.write('\n')
