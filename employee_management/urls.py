"""
Main URL configuration for employee_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/dashboard/', include('dashboard.urls')),  # Day 4: Dashboard & Day 6: Tasks/Projects
    path('api/notifications/', include('notifications.urls')),  # Day 7: Notifications
    path('api/leaves/', include('leaves.urls')),  # Day 8: Leave Management
    path('api/attendance/', include('attendance.urls')),  # Day 10: Attendance Management
    path('api/chat/', include('chat.urls')),  # Day 12: Chat System
    path('api/hr/', include('hr_profile.urls')),  # Day 15: Employee Profile & Onboarding
    path('api/payroll/', include('hr_payroll.urls')),  # Day 16: Payroll Management
    path('api/expenses/', include('hr_expenses.urls')),  # Day 17: Expense & Reimbursement Management
    path('api/performance/', include('hr_performance.urls')),  # Day 18: Performance Management - Goals & OKRs
    path('api/reviews/', include('hr_reviews.urls')),  # Day 19: Performance Reviews & Feedback
    path('api/lms/', include('hr_lms.urls')),  # Day 20: Learning Management System (LMS)
    path('api/logs/', include('audit_trail.urls')),  # Day 22: Activity Logs & Audit Trail
    path('api/compliance/', include('compliance.urls')),  # Day 23: Compliance & Policy Management
    path('api/documents/', include('documents.urls')),  # Day 24: Document Management System
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
