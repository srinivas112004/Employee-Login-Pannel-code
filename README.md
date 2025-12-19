# Employee Management System - Django Backend

## 🎯 Project Overview
A comprehensive Employee Login Panel with enterprise-grade features for MNC-level requirements.

## 👨‍💻 For Backend Developer Intern
This project is structured as a **30-day learning and development journey**. Each day builds upon the previous day's work.

## 📋 Prerequisites
- Python 3.9+
- pip (Python package manager)
- Postman (for API testing)
- Git
- Basic understanding of Python

## 🚀 Quick Start (Day 1)

### Step 1: Set up Virtual Environment
```bash
# Navigate to project directory
cd "c:\Users\srini\OneDrive\Desktop\Emp"

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set up Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 5: Run Development Server
```bash
python manage.py runserver
```

The server will start at `http://localhost:8000`

## 📁 Project Structure
```
Emp/
├── employee_management/     # Main project folder
│   ├── settings.py         # Project settings
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI config
├── authentication/         # Day 1-2: Authentication & User Management
├── dashboard/             # Day 4,6: Employee Dashboard & Task/Project Management
├── notifications/         # Day 7: Notifications & Reminders
├── leaves/                # Day 8-9: Leave & Attendance Management
├── attendance/            # Day 10: Attendance Management System
├── chat/                  # Day 12-14: Chat & Real-time Communication
├── hr_profile/            # Day 15: Employee Profile & Onboarding
├── hr_payroll/           # Future: HR & Payroll Management
├── performance/          # Future: Performance & KPI Tracking
├── learning/             # Future: Learning & Development
├── compliance/           # Future: Compliance & Policy
├── documents/            # Future: Document Management
├── analytics/            # Future: Analytics & Reporting
├── requirements.txt      # Python dependencies
├── DAILY_ROADMAP.md     # 30-day development plan
└── POSTMAN_TESTING_GUIDE.md  # API testing guide
```

## 📚 Documentation Files
1. **DAILY_ROADMAP.md** - Your day-by-day development guide
2. **POSTMAN_TESTING_GUIDE.md** - How to test APIs in Postman
3. **This README** - Project overview and setup

## 🔐 Security Features Implemented
- JWT Authentication
- Role-Based Access Control (RBAC)
- Password hashing with Django's built-in system
- CORS configuration
- Environment variable management
- Session security

## 📊 Tech Stack
- **Framework**: Django 4.2+
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API**: Django REST Framework
- **Real-time**: Django Channels (WebSocket)
- **Caching**: Redis
- **File Storage**: AWS S3 / Local storage

## 👥 Team Roles
- **You**: Backend Developer (Django APIs)
- **Frontend Team**: React/Angular integration
- **Manager**: Reviews daily progress

## 📈 Daily Workflow
1. Check `DAILY_ROADMAP.md` for today's tasks
2. Implement the features
3. Test using Postman (refer to `POSTMAN_TESTING_GUIDE.md`)
4. Commit your code
5. Demo to manager

## 🆘 Getting Help
- Read Django documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Stack Overflow for specific issues

## 📝 License
Internal Project - Company Confidential

---
**Good luck with your internship! 🚀**
