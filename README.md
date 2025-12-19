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
Employee Login Panel/
├── manage.py
├── requirements.txt
├── README.md
├── employee_management/     # Main Django project settings
├── authentication/          # User auth, JWT, 2FA
├── dashboard/               # Dashboard & task management
├── notifications/           # Notifications system
├── leaves/                  # Leave management
├── attendance/              # Attendance tracking
├── chat/                    # Real-time chat (WebSocket)
├── hr_profile/              # Employee profiles
├── hr_payroll/              # Payroll management
├── hr_performance/          # Performance tracking
├── hr_reviews/              # Performance reviews
├── hr_lms/                  # Learning management
├── hr_expenses/             # Expense management
├── compliance/              # Policy & compliance
├── documents/               # Document management
├── audit_trail/             # Audit logging
├── media/                   # Uploaded files
└── frontend/                # React frontend (Vite)
    ├── src/
    │   ├── components/      # Reusable UI components
    │   ├── pages/           # Page components
    │   ├── context/         # React context
    │   ├── hooks/           # Custom hooks
    │   └── utils/           # Utilities
    └── public/
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
