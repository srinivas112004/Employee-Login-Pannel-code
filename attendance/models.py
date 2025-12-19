from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()


class Shift(models.Model):
    """Employee shift timings"""
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_minutes = models.IntegerField(default=15, help_text="Grace period for late coming")
    total_hours = models.DecimalField(max_digits=4, decimal_places=2, help_text="Total work hours")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class Attendance(models.Model):
    """Daily attendance records with geo-tagging"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('on_leave', 'On Leave'),
        ('work_from_home', 'Work From Home'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Check-in details
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_location = models.CharField(max_length=255, blank=True, help_text="Latitude, Longitude")
    check_in_address = models.TextField(blank=True)
    check_in_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Check-out details
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_location = models.CharField(max_length=255, blank=True, help_text="Latitude, Longitude")
    check_out_address = models.TextField(blank=True)
    check_out_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    is_late = models.BooleanField(default=False)
    late_by_minutes = models.IntegerField(default=0)
    work_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0, help_text="Total work hours")
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    
    # Notes and remarks
    remarks = models.TextField(blank=True)
    is_regularized = models.BooleanField(default=False)
    regularized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='regularized_attendance')
    regularization_reason = models.TextField(blank=True)
    regularized_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-check_in_time']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.status}"

    def save(self, *args, **kwargs):
        # Calculate work hours if both check-in and check-out are present
        if self.check_in_time and self.check_out_time:
            time_diff = self.check_out_time - self.check_in_time
            hours = time_diff.total_seconds() / 3600
            self.work_hours = round(hours, 2)
            
            # Calculate overtime if shift is assigned
            if self.shift:
                shift_hours = float(self.shift.total_hours)
                if hours > shift_hours:
                    self.overtime_hours = round(hours - shift_hours, 2)
            
            # Update status
            if self.work_hours >= 4:
                self.status = 'present'
            elif self.work_hours > 0:
                self.status = 'half_day'
        
        # Check if late
        if self.check_in_time and self.shift:
            check_in_time_only = self.check_in_time.time()
            shift_start = self.shift.start_time
            
            # Convert to datetime for comparison
            today = timezone.now().date()
            check_in_dt = datetime.combine(today, check_in_time_only)
            shift_start_dt = datetime.combine(today, shift_start)
            
            if check_in_dt > shift_start_dt:
                diff = (check_in_dt - shift_start_dt).total_seconds() / 60
                grace_period = self.shift.grace_period_minutes
                
                if diff > grace_period:
                    self.is_late = True
                    self.late_by_minutes = int(diff)
        
        super().save(*args, **kwargs)


class AttendanceRegularization(models.Model):
    """Attendance regularization requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='regularization_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_regularization_requests')
    reason = models.TextField()
    
    # What needs to be corrected
    requested_check_in = models.DateTimeField(null=True, blank=True)
    requested_check_out = models.DateTimeField(null=True, blank=True)
    requested_status = models.CharField(max_length=20, choices=Attendance.STATUS_CHOICES, null=True, blank=True)
    
    # Approval details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_regularizations')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requested_by.email} - {self.attendance.date} - {self.status}"


class WorkFromHomeRequest(models.Model):
    """WFH requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wfh_requests')
    date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_wfh_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.email} - WFH on {self.date} - {self.status}"
