# hr_payroll/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalaryStructureViewSet,
    EmployeeSalaryViewSet,
    PayslipViewSet,
    SalaryHistoryViewSet,
    DeductionViewSet
)

router = DefaultRouter()
router.register(r'salary-structures', SalaryStructureViewSet, basename='salary-structure')
router.register(r'employee-salaries', EmployeeSalaryViewSet, basename='employee-salary')
router.register(r'payslips', PayslipViewSet, basename='payslip')
router.register(r'salary-history', SalaryHistoryViewSet, basename='salary-history')
router.register(r'deductions', DeductionViewSet, basename='deduction')

urlpatterns = router.urls
