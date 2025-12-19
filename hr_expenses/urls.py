# hr_expenses/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExpenseCategoryViewSet,
    ExpenseClaimViewSet,
    ReceiptViewSet,
    ReimbursementHistoryViewSet
)

router = DefaultRouter()
router.register(r'categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'claims', ExpenseClaimViewSet, basename='expense-claim')
router.register(r'receipts', ReceiptViewSet, basename='receipt')
router.register(r'history', ReimbursementHistoryViewSet, basename='reimbursement-history')

urlpatterns = [
    path('', include(router.urls)),
]
