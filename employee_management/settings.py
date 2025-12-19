"""
Django settings for employee_management project.
"""

from pathlib import Path
from datetime import timedelta
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-change-this-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'daphne',  # Day 13: ASGI server for WebSockets (must be first)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # For token blacklist on logout
    'corsheaders',
    'django_filters',
    'django_celery_beat',  # Day 7: Celery Beat scheduler
    'channels',  # Day 13: WebSocket support
    
    # Local apps
    'authentication',
    'dashboard',  # Day 4: Employee Dashboard & Day 6: Task/Project Management
    'notifications',  # Day 7: Task Notifications & Reminders
    'leaves',  # Day 8: Leave Management
    'attendance',  # Day 10: Attendance Management
    'chat',  # Day 12-13: Chat System with WebSockets
    'hr_profile',  # Day 15: Employee Profile & Onboarding
    'hr_payroll',  # Day 16: Payroll Management
    'hr_expenses',  # Day 17: Expense & Reimbursement Management
    'hr_performance',  # Day 18: Performance Management - Goals & OKRs
    'hr_reviews',  # Day 19: Performance Reviews & Feedback
    'hr_lms',  # Day 20: Learning Management System (LMS)
    'audit_trail',  # Day 22: Activity Logs & Audit Trail (MongoDB)
    'compliance',  # Day 23: Compliance & Policy Management
    'documents',  # Day 24: Document Management System
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS headers
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'authentication.middleware.ActiveSessionMiddleware',  # Check active sessions
    'audit_trail.middleware.ActivityLoggingMiddleware',  # Day 22: Activity logging
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'employee_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'employee_management.wsgi.application'

# Day 13: ASGI Application for WebSockets
ASGI_APPLICATION = 'employee_management.asgi.application'

# Day 13: Channel Layers Configuration (using Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Database
# Using SQLite for development. In production, use PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# MongoDB Configuration for Chat (using pymongo directly)
MONGODB_SETTINGS = {
    'host': 'localhost',
    'port': 27017,
    'db_name': 'employee_chat_db',
    'username': '',  # Add if MongoDB has authentication
    'password': '',  # Add if MongoDB has authentication
}

# MongoDB Configuration for Audit Trail (Day 22)
MONGODB_AUDIT_SETTINGS = {
    'host': 'localhost',
    'port': 27017,
    'db_name': 'employee_audit_db',
    'username': '',  # Add if MongoDB has authentication
    'password': '',  # Add if MongoDB has authentication
    'collection_name': 'activity_logs',
}

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploaded files)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # 24 hours for development
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Settings (Allow frontend to access backend)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://localhost:4200",  # Angular default
    "http://localhost:8080",  # Vue default
]

CORS_ALLOW_CREDENTIALS = True

# For development, allow all origins (Change in production!)
CORS_ALLOW_ALL_ORIGINS = True

# Security Settings (Enhance in production)
SESSION_COOKIE_SECURE = False  # Set True in production (HTTPS)
CSRF_COOKIE_SECURE = False  # Set True in production
SECURE_SSL_REDIRECT = False  # Set True in production

# Session timeout (30 minutes of inactivity)
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ==============================================================================
# EMAIL CONFIGURATION (Day 2)
# ==============================================================================

# SMTP Configuration - Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'natureglow2004@gmail.com'
EMAIL_HOST_PASSWORD = 'oyor liyf szgd ejxe'
DEFAULT_FROM_EMAIL = 'Employee Management System <natureglow2004@gmail.com>'

# Email settings
EMAIL_SUBJECT_PREFIX = '[EMS] '
EMAIL_TIMEOUT = 10  # seconds

# ==============================================================================
# CELERY CONFIGURATION (Day 7)
# ==============================================================================

# Celery broker and result backend (using Redis)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Celery settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Celery Beat scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Task time limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Task retry settings
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# ==============================================================================
# MEDIA FILES CONFIGURATION (Day 15)
# ==============================================================================

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB


