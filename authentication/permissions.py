"""
Authentication App - Permissions
Custom permission classes for role-based access control.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class to check if user is an admin.
    """
    message = "You must be an admin to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsHR(permissions.BasePermission):
    """
    Permission class to check if user is HR.
    """
    message = "You must be an HR personnel to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'hr'


class IsManager(permissions.BasePermission):
    """
    Permission class to check if user is a manager.
    """
    message = "You must be a manager to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'manager'


class IsAdminOrHR(permissions.BasePermission):
    """
    Permission class to check if user is admin or HR.
    """
    message = "You must be an admin or HR personnel to perform this action."
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['admin', 'hr'])


class IsEmployee(permissions.BasePermission):
    """
    Permission class to check if user is an employee.
    """
    message = "You must be an employee to perform this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'employee'


class IsManagerOrAbove(permissions.BasePermission):
    """
    Permission class to check if user is manager, HR, or admin.
    """
    message = "You must be a manager, HR, or admin to perform this action."
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['manager', 'hr', 'admin'])


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class to allow owners to edit, others to only read.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user or obj == request.user
