# Employee Management System

## 🎯 Project Overview
A comprehensive Employee Management System with enterprise-grade features including authentication, HR management, real-time chat, payroll, performance tracking, and more. Built with Django REST Framework backend and React (Vite) frontend.

## 📋 Prerequisites
- Python 3.9+
- Node.js 18+
- pip (Python package manager)
- Redis (for WebSockets & Celery)
- MongoDB (for Chat & Audit Logs)
- Git

## 🚀 Quick Start

### Backend Setup

```bash
# Navigate to project directory
cd "Employee Login Pannel Code"

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python manage.py makemigrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Backend server runs at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at `http://localhost:5173`

### Additional Services

```bash
# Start Redis (required for WebSocket chat)
redis-server

# Start Celery worker (for background tasks)
celery -A employee_management worker -l INFO

# Start Celery Beat (for scheduled tasks)
celery -A employee_management beat -l INFO
```

## 📁 Project Structure

```
Employee Management System/
├── manage.py
├── requirements.txt
├── README.md
│
├── employee_management/          # Django Project Configuration
│   ├── settings.py               # Project settings
│   ├── urls.py                   # Main URL routing
│   ├── asgi.py                   # ASGI config (WebSockets)
│   ├── wsgi.py                   # WSGI config
│   ├── celery.py                 # Celery configuration
│   └── db_router.py              # Database routing
│
├── authentication/               # User Authentication Module
│   ├── models.py                 # User, Device, Session models
│   ├── views.py                  # Auth endpoints
│   ├── serializers.py            # Data serialization
│   ├── permissions.py            # RBAC permissions
│   ├── middleware.py             # Session middleware
│   ├── device_utils.py           # Device fingerprinting
│   └── email_utils.py            # Email utilities
│
├── dashboard/                    # Dashboard & Project Management
│   ├── models.py                 # Task, Project, Milestone models
│   ├── views.py                  # Dashboard endpoints
│   └── management/               # Custom management commands
│
├── notifications/                # Notification System
│   ├── models.py                 # Notification, Preferences
│   └── views.py                  # Notification endpoints
│
├── leaves/                       # Leave Management
│   ├── models.py                 # Leave, LeaveType, LeaveBalance
│   └── views.py                  # Leave CRUD operations
│
├── attendance/                   # Attendance Tracking
│   ├── models.py                 # Shift, Attendance, WFH models
│   └── views.py                  # Attendance endpoints
│
├── chat/                         # Real-time Chat (WebSocket)
│   ├── models.py                 # ChatRoom, Message models
│   ├── consumers.py              # WebSocket consumers
│   ├── routing.py                # WebSocket routing
│   ├── mongo_service.py          # MongoDB integration
│   └── views.py                  # Chat REST endpoints
│
├── hr_profile/                   # Employee Profile & Onboarding
│   ├── models.py                 # Profile, Documents, History
│   └── views.py                  # Profile management
│
├── hr_payroll/                   # Payroll Management
│   ├── models.py                 # Salary, Payslip, Deductions
│   └── views.py                  # Payroll endpoints
│
├── hr_expenses/                  # Expense & Reimbursement
│   ├── models.py                 # Expense, Receipt models
│   └── views.py                  # Expense management
│
├── hr_performance/               # Performance Management
│   ├── models.py                 # Goals, KPIs, Progress
│   └── views.py                  # Performance tracking
│
├── hr_reviews/                   # Performance Reviews
│   ├── models.py                 # Review cycles, Feedback
│   └── views.py                  # Review management
│
├── hr_lms/                       # Learning Management System
│   ├── models.py                 # Course, Quiz, Certificate
│   └── views.py                  # LMS endpoints
│
├── audit_trail/                  # Activity Logging (MongoDB)
│   ├── models.py                 # ActivityLog model
│   ├── middleware.py             # Auto-logging middleware
│   ├── mongodb_utils.py          # MongoDB connection
│   └── views.py                  # Log viewing endpoints
│
├── compliance/                   # Policy & Compliance
│   ├── models.py                 # Policy, Acknowledgment
│   └── views.py                  # Compliance management
│
├── documents/                    # Document Management
│   ├── models.py                 # Document, Category, Share
│   └── views.py                  # Document CRUD
│
├── media/                        # Uploaded Files Storage
│
└── frontend/                     # React Frontend (Vite)
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/                  # API service layer
        ├── components/           # Reusable UI components
        ├── pages/                # Page components
        ├── context/              # React context providers
        ├── hooks/                # Custom React hooks
        └── utils/                # Utility functions
```

## 🔐 Security Features
- **JWT Authentication** with token blacklisting
- **Role-Based Access Control (RBAC)** - Admin, HR, Manager, Employee, Intern
- **Two-Factor Authentication (2FA)** with OTP
- **Device Management** - Fingerprinting & trusted devices
- **Session Management** - Active session tracking & remote logout
- **Email Verification** for new accounts
- **Password Reset** with secure OTP flow
- **Activity Audit Logging** (MongoDB)
- **CORS Configuration**

## 📊 Tech Stack

### Backend
- **Framework**: Django 4.2.7
- **API**: Django REST Framework 3.14.0
- **Authentication**: JWT (djangorestframework-simplejwt 5.3.0)
- **WebSockets**: Django Channels 4.0.0
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **NoSQL**: MongoDB (Chat & Audit Trail via pymongo 4.6.0)
- **Caching/Message Broker**: Redis 5.0.1
- **Task Queue**: Celery 5.3.4 with django-celery-beat
- **File Storage**: Local / AWS S3 (boto3)

### Frontend
- **Framework**: React 19.1.1
- **Build Tool**: Vite 7.1.12
- **Routing**: React Router DOM 7.9.4
- **UI**: Bootstrap 5.3.8 + React Bootstrap
- **HTTP Client**: Axios 1.13.2
- **WebSocket**: Socket.IO Client 4.8.1
- **Icons**: Bootstrap Icons, React Icons

## 🌐 API Endpoints

### Authentication (`/api/auth/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login/` | User login with JWT |
| POST | `/logout/` | Logout & blacklist token |
| POST | `/token/refresh/` | Refresh access token |
| GET/PUT | `/profile/` | Get/Update user profile |
| POST | `/change-password/` | Change password |
| GET | `/users/` | List all users (admin) |
| POST | `/send-otp/` | Send OTP to email |
| POST | `/verify-otp/` | Verify OTP code |
| POST | `/resend-verification/` | Resend email verification |
| POST | `/password-reset/request/` | Request password reset |
| POST | `/password-reset/confirm/` | Confirm password reset |
| POST | `/2fa/toggle/` | Enable/disable 2FA |
| GET | `/devices/` | List user devices |
| DELETE | `/devices/<id>/` | Remove device |
| POST | `/devices/trust/` | Trust a device |
| GET | `/sessions/` | List active sessions |
| POST | `/sessions/<id>/logout/` | Logout specific session |
| POST | `/sessions/logout-all/` | Logout all sessions |

### Dashboard (`/api/dashboard/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/summary/` | Dashboard summary |
| GET | `/tasks-summary/` | Task statistics |
| GET | `/leave-balance/` | User leave balance |
| GET/POST | `/announcements/` | List/create announcements |
| GET/PUT/DELETE | `/announcements/<id>/` | Announcement details |
| GET/POST | `/tasks/` | List/create tasks |
| GET/PUT/DELETE | `/tasks/<id>/` | Task details |
| GET/POST | `/projects/` | List/create projects |
| GET/PUT/DELETE | `/projects/<id>/` | Project details |
| GET/POST | `/projects/<id>/milestones/` | Project milestones |
| GET/PUT/DELETE | `/milestones/<id>/` | Milestone details |
| GET/POST | `/tasks/<id>/subtasks/` | Task subtasks |
| POST | `/attachments/` | Upload file attachment |
| DELETE | `/attachments/<id>/` | Delete attachment |

### Leave Management (`/api/leaves/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/balance/` | User leave balance |
| GET/POST | `/leaves/` | List/apply for leaves |
| GET/PUT/DELETE | `/leaves/<id>/` | Leave details |
| GET/POST | `/types/` | Leave types |
| GET/PUT/DELETE | `/types/<id>/` | Leave type details |

### Attendance (`/api/attendance/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/shifts/` | Shift management |
| GET/PUT/DELETE | `/shifts/<id>/` | Shift details |
| GET/POST | `/attendance/` | Attendance records |
| GET/PUT/DELETE | `/attendance/<id>/` | Attendance details |
| GET/POST | `/regularizations/` | Attendance regularizations |
| GET/PUT/DELETE | `/regularizations/<id>/` | Regularization details |
| GET/POST | `/wfh-requests/` | Work from home requests |
| GET/PUT/DELETE | `/wfh-requests/<id>/` | WFH request details |

### Chat System (`/api/chat/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/rooms/` | Chat rooms |
| GET/PUT/DELETE | `/rooms/<id>/` | Room details |
| GET/POST | `/messages/` | Chat messages |
| GET/PUT/DELETE | `/messages/<id>/` | Message details |
| GET/POST | `/channels/` | Chat channels |
| GET | `/online-status/` | Online user status |
| GET | `/notifications/` | Chat notifications |
| POST | `/files/` | File uploads |

### HR Profile (`/api/hr/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/employees/` | Employee profiles |
| GET/PUT/DELETE | `/employees/<id>/` | Profile details |
| GET/POST | `/documents/` | Employee documents |
| GET/PUT/DELETE | `/documents/<id>/` | Document details |
| GET/POST | `/onboarding/` | Onboarding checklists |
| GET/PUT/DELETE | `/onboarding/<id>/` | Checklist details |
| GET/POST | `/employment-history/` | Employment history |
| GET/PUT/DELETE | `/employment-history/<id>/` | History details |

### Payroll (`/api/payroll/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/salary-structures/` | Salary structures |
| GET/PUT/DELETE | `/salary-structures/<id>/` | Structure details |
| GET/POST | `/employee-salaries/` | Employee salaries |
| GET/PUT/DELETE | `/employee-salaries/<id>/` | Salary details |
| GET/POST | `/payslips/` | Payslips |
| GET/PUT/DELETE | `/payslips/<id>/` | Payslip details |
| GET | `/salary-history/` | Salary history |
| GET/POST | `/deductions/` | Deductions |

### Expenses (`/api/expenses/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/categories/` | Expense categories |
| GET/PUT/DELETE | `/categories/<id>/` | Category details |
| GET/POST | `/claims/` | Expense claims |
| GET/PUT/DELETE | `/claims/<id>/` | Claim details |
| GET/POST | `/receipts/` | Receipts |
| GET/PUT/DELETE | `/receipts/<id>/` | Receipt details |
| GET | `/history/` | Reimbursement history |

### Performance (`/api/performance/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/categories/` | Goal categories |
| GET/PUT/DELETE | `/categories/<id>/` | Category details |
| GET/POST | `/goals/` | Goals management |
| GET/PUT/DELETE | `/goals/<id>/` | Goal details |
| GET/POST | `/kpis/` | Key Performance Indicators |
| GET/PUT/DELETE | `/kpis/<id>/` | KPI details |
| GET/POST | `/progress-updates/` | Progress updates |
| GET/POST | `/milestones/` | Goal milestones |

### Reviews (`/api/reviews/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/review-cycles/` | Review cycles |
| GET/PUT/DELETE | `/review-cycles/<id>/` | Cycle details |
| GET/POST | `/reviews/` | Performance reviews |
| GET/PUT/DELETE | `/reviews/<id>/` | Review details |
| GET/POST | `/self-assessments/` | Self assessments |
| GET/POST | `/manager-reviews/` | Manager reviews |
| GET/POST | `/peer-feedback/` | Peer feedback |

### LMS (`/api/lms/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/courses/` | Courses |
| GET/PUT/DELETE | `/courses/<id>/` | Course details |
| GET/POST | `/modules/` | Course modules |
| GET/PUT/DELETE | `/modules/<id>/` | Module details |
| GET/POST | `/enrollments/` | Course enrollments |
| GET/PUT/DELETE | `/enrollments/<id>/` | Enrollment details |
| GET/POST | `/progress/` | Module progress |
| GET/POST | `/quizzes/` | Quizzes |
| GET/PUT/DELETE | `/quizzes/<id>/` | Quiz details |
| GET/POST | `/quiz-questions/` | Quiz questions |
| GET/POST | `/certificates/` | Certificates |
| GET/POST | `/skills/` | Skills catalog |
| GET/POST | `/user-skills/` | User skills |

### Audit Trail (`/api/logs/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/activity/` | Activity logs |
| GET | `/activity/<id>/` | Log details |
| GET | `/audit/` | Audit logs |
| GET | `/audit/<id>/` | Audit details |

### Compliance (`/api/compliance/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/categories/` | Policy categories |
| GET/PUT/DELETE | `/categories/<id>/` | Category details |
| GET/POST | `/policies/` | Policies |
| GET/PUT/DELETE | `/policies/<id>/` | Policy details |
| GET/POST | `/acknowledgments/` | Policy acknowledgments |

### Documents (`/api/documents/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/categories/` | Document categories |
| GET/PUT/DELETE | `/categories/<id>/` | Category details |
| GET/POST | `/documents/` | Documents |
| GET/PUT/DELETE | `/documents/<id>/` | Document details |
| GET/POST | `/shares/` | Document shares |

### Notifications (`/api/notifications/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List notifications |
| GET/PUT | `/<id>/` | Notification details |
| GET/PUT | `/preferences/` | Notification preferences |
| GET/POST | `/escalations/` | Task escalations |

## 🖥️ Frontend Pages

| Page | Description |
|------|-------------|
| Login | User authentication |
| Dashboard | Main dashboard with summary |
| Profile | User profile management |
| ChangePassword | Password change form |
| UserList | User management (admin) |
| TasksPage | Task management |
| ProjectManagement | Projects & milestones |
| AnnouncementsPage | Company announcements |
| LeaveApply | Leave application |
| LeaveHistory | Leave history |
| LeaveDashboard | Leave overview |
| AttendancePage | Attendance tracking |
| ChatPage | Real-time messaging |
| NotificationsPage | Notification center |
| PayrollPanel | Payroll management |
| ExpensesPanel | Expense claims |
| PerformancePanel | Goals & KPIs |
| ReviewsPanel | Performance reviews |
| LMSPanel | Learning courses |
| CompliancePanel | Policies |
| DocumentsPanel | Document management |
| LogsPanel | Activity logs |
| HROverview | HR dashboard |

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=employee_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=employee_chat_db

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket
```

## 👥 User Roles

| Role | Permissions |
|------|-------------|
| Admin | Full system access |
| HR | HR module access, user management |
| Manager | Team management, approvals |
| Employee | Standard access |
| Intern | Limited access |

## 🧪 Testing

```bash
# Run backend tests
python manage.py test

# Run frontend tests
cd frontend
npm run test
```

## 📦 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis server
- [ ] Configure MongoDB
- [ ] Set strong `SECRET_KEY`
- [ ] Configure email settings
- [ ] Set up Celery workers
- [ ] Configure HTTPS/SSL
- [ ] Set up static file serving (nginx/whitenoise)
- [ ] Configure CORS for production domain

### Docker (Optional)
```bash
docker-compose up --build
```

## 📝 License
Internal Project - Company Confidential

---
**Built with ❤️ using Django & React**
