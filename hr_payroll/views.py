# hr_payroll/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Sum, Avg
from django.http import FileResponse, HttpResponse
from decimal import Decimal
from datetime import datetime
import io

from .models import (
    SalaryStructure, EmployeeSalary, Payslip, 
    SalaryHistory, Deduction
)
from .serializers import (
    SalaryStructureSerializer, EmployeeSalarySerializer,
    PayslipSerializer, PayslipListSerializer,
    SalaryHistorySerializer, DeductionSerializer,
    PayrollGenerationSerializer
)
from hr_profile.models import EmployeeProfile


class SalaryStructureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for salary structure templates
    - Admin/HR: Full CRUD access
    - Others: Read-only
    """
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin/HR can see all structures
        if user.role in ['admin', 'hr']:
            return SalaryStructure.objects.all()
        
        # Others can only see active structures
        return SalaryStructure.objects.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        """Create salary structure - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can create salary structures.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update salary structure - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can update salary structures.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete salary structure - Admin only"""
        if request.user.role != 'admin':
            return Response(
                {'detail': 'Only Admin can delete salary structures.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class EmployeeSalaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for employee salary assignments
    - Admin/HR: Full access
    - Employee: Can view own salary
    """
    serializer_class = EmployeeSalarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter by employee parameter (for admin/HR filtering)
        employee_id = self.request.query_params.get('employee', None)
        
        # Admin/HR can see all employee salaries or filter by specific employee
        if user.role in ['admin', 'hr', 'manager']:
            if employee_id:
                # Admin/HR filtering by specific employee (can be User ID or EmployeeProfile ID)
                try:
                    employee_profile = EmployeeProfile.objects.get(id=employee_id)
                    queryset = EmployeeSalary.objects.filter(employee=employee_profile)
                except EmployeeProfile.DoesNotExist:
                    # Assume it's a User ID, try to find the profile
                    try:
                        employee_profile = EmployeeProfile.objects.get(user_id=employee_id)
                        queryset = EmployeeSalary.objects.filter(employee=employee_profile)
                    except EmployeeProfile.DoesNotExist:
                        # No profile found for this user, return empty queryset
                        queryset = EmployeeSalary.objects.none()
            else:
                queryset = EmployeeSalary.objects.all()
        else:
            # Employees can see only their own salary (ignore employee parameter)
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                queryset = EmployeeSalary.objects.filter(employee=employee_profile)
            except EmployeeProfile.DoesNotExist:
                queryset = EmployeeSalary.objects.none()
        
        return queryset.select_related(
            'employee__user', 
            'salary_structure', 
            'created_by'
        ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Assign salary to employee - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can assign salaries.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle if employee is provided as user ID instead of profile ID
        employee_id = request.data.get('employee')
        profile = None
        if employee_id:
            try:
                # First check if it's an EmployeeProfile ID
                profile = EmployeeProfile.objects.filter(id=employee_id).first()
                
                if not profile:
                    # Try to find profile by user ID
                    from authentication.models import User
                    user = User.objects.filter(id=employee_id).first()
                    if user:
                        profile = EmployeeProfile.objects.filter(user=user).first()
                        if not profile:
                            # Auto-create employee profile for this user
                            from datetime import date
                            profile = EmployeeProfile.objects.create(
                                user=user,
                                employee_id=f'EMP-{user.id:04d}',
                                department=user.role.upper() if user.role else 'GENERAL',
                                designation=user.role.title() if user.role else 'Employee',
                                joining_date=date.today(),
                                date_of_birth=date(1990, 1, 1),  # Default DOB
                                gender='O',  # Other
                                marital_status='SINGLE',
                                phone_primary='+1234567890'  # Default phone
                            )
                
                # Always update request data with correct profile ID
                if profile:
                    request.data['employee'] = profile.id
                    
                    # Check if employee already has a salary record (OneToOneField)
                    existing_salary = EmployeeSalary.objects.filter(employee=profile).first()
                    if existing_salary:
                        # Update existing record instead of creating new one
                        serializer = self.get_serializer(existing_salary, data=request.data, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        return Response({
                            'detail': 'Employee salary updated successfully',
                            'data': serializer.data
                        }, status=status.HTTP_200_OK)
                        
            except Exception as e:
                import traceback
                print(f"Error finding/creating employee profile: {str(e)}")
                print(traceback.format_exc())
                return Response(
                    {'detail': f'Error finding/creating employee profile: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create new salary record
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            print(f"Error creating salary: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'detail': f'Error creating salary: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """Update employee salary - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can update salaries.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_salary(self, request):
        """Get current user's salary details"""
        try:
            employee_profile = EmployeeProfile.objects.get(user=request.user)
            salary = EmployeeSalary.objects.filter(
                employee=employee_profile,
                is_active=True
            ).first()
            
            if not salary:
                return Response(
                    {'detail': 'No active salary found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(salary)
            return Response(serializer.data)
            
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'detail': 'Employee profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class PayslipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payslip management
    - Admin/HR: Full access
    - Employee: Can view own payslips
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PayslipListSerializer
        return PayslipSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter by employee parameter (for admin/HR filtering)
        employee_id = self.request.query_params.get('employee', None)
        
        # Admin/HR can see all payslips or filter by specific employee
        if user.role in ['admin', 'hr']:
            if employee_id:
                # Admin/HR filtering by specific employee (can be User ID or EmployeeProfile ID)
                try:
                    employee_profile = EmployeeProfile.objects.get(id=employee_id)
                    queryset = Payslip.objects.filter(employee=employee_profile)
                except EmployeeProfile.DoesNotExist:
                    # Assume it's a User ID, try to find the profile
                    try:
                        employee_profile = EmployeeProfile.objects.get(user_id=employee_id)
                        queryset = Payslip.objects.filter(employee=employee_profile)
                    except EmployeeProfile.DoesNotExist:
                        # No profile found for this user, return empty queryset
                        queryset = Payslip.objects.none()
            else:
                queryset = Payslip.objects.all()
        else:
            # Employees can see only their own payslips (ignore employee parameter)
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                queryset = Payslip.objects.filter(employee=employee_profile)
            except EmployeeProfile.DoesNotExist:
                queryset = Payslip.objects.none()
        
        # Filter by month/year
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        if month:
            queryset = queryset.filter(month=month)
        if year:
            queryset = queryset.filter(year=year)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('employee', 'employee_salary', 'generated_by', 'approved_by')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate payslips for employees - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can generate payslips.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PayrollGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        month = serializer.validated_data['month']
        year = serializer.validated_data['year']
        employee_ids = serializer.validated_data.get('employee_ids', [])
        total_working_days = serializer.validated_data.get('total_working_days', 26)
        
        # Get employees to generate payslips for
        if employee_ids:
            employees = EmployeeProfile.objects.filter(id__in=employee_ids)
        else:
            # Get all employees with active salaries
            employees = EmployeeProfile.objects.filter(
                salary__is_active=True,
                user__is_active=True
            ).distinct()
        
        generated_payslips = []
        errors = []
        
        for employee in employees:
            try:
                # Check if payslip already exists
                if Payslip.objects.filter(employee=employee, month=month, year=year).exists():
                    errors.append(f"{employee.employee_id}: Payslip already exists")
                    continue
                
                # Get active salary
                employee_salary = EmployeeSalary.objects.filter(
                    employee=employee,
                    is_active=True
                ).first()
                
                if not employee_salary:
                    errors.append(f"{employee.employee_id}: No active salary found")
                    continue
                
                # Calculate salary components (pro-rated for days worked)
                days_ratio = Decimal(total_working_days) / Decimal(total_working_days)
                
                basic = employee_salary.basic_salary * days_ratio
                hra = (employee_salary.custom_hra or employee_salary.salary_structure.hra) * days_ratio
                transport = (employee_salary.custom_transport or employee_salary.salary_structure.transport_allowance) * days_ratio
                medical = (employee_salary.custom_medical or employee_salary.salary_structure.medical_allowance) * days_ratio
                special = (employee_salary.custom_special or employee_salary.salary_structure.special_allowance) * days_ratio
                bonus = employee_salary.salary_structure.bonus * days_ratio
                
                gross = basic + hra + transport + medical + special + bonus
                
                # Calculate deductions
                pf = (basic * employee_salary.salary_structure.pf_employee / 100)
                esi = (gross * employee_salary.salary_structure.esi_employee / 100) if gross <= 21000 else 0
                pt = employee_salary.salary_structure.professional_tax
                tds = (gross * employee_salary.salary_structure.tds / 100)
                
                # Get additional deductions
                additional_deductions = Deduction.objects.filter(
                    employee=employee,
                    is_active=True,
                    start_year__lte=year,
                    start_month__lte=month
                ).filter(
                    Q(end_year__gte=year) | Q(end_year__isnull=True)
                )
                
                loan_deduction = sum([d.installment_amount for d in additional_deductions])
                
                total_deductions = pf + esi + pt + tds + Decimal(loan_deduction)
                net = gross - total_deductions
                
                # Create payslip
                payslip = Payslip.objects.create(
                    employee=employee,
                    employee_salary=employee_salary,
                    month=month,
                    year=year,
                    total_working_days=total_working_days,
                    days_worked=total_working_days,
                    days_absent=0,
                    basic_salary=basic,
                    hra=hra,
                    transport_allowance=transport,
                    medical_allowance=medical,
                    special_allowance=special,
                    bonus=bonus,
                    overtime_pay=0,
                    incentives=0,
                    pf_employee=pf,
                    esi_employee=esi,
                    professional_tax=pt,
                    tds=tds,
                    loan_deduction=loan_deduction,
                    other_deductions=0,
                    gross_salary=gross,
                    total_deductions=total_deductions,
                    net_salary=net,
                    status='GENERATED',
                    generated_by=request.user
                )
                
                generated_payslips.append(payslip)
                
            except Exception as e:
                errors.append(f"{employee.employee_id}: {str(e)}")
        
        return Response({
            'message': f'Generated {len(generated_payslips)} payslips',
            'generated': [p.id for p in generated_payslips],
            'errors': errors
        }, status=status.HTTP_201_CREATED if generated_payslips else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve payslip - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can approve payslips.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payslip = self.get_object()
        
        if payslip.status == 'APPROVED':
            return Response(
                {'detail': 'Payslip is already approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payslip.status = 'APPROVED'
        payslip.approved_by = request.user
        payslip.approved_at = timezone.now()
        payslip.save()
        
        serializer = self.get_serializer(payslip)
        return Response({
            'message': 'Payslip approved successfully',
            'payslip': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark payslip as paid - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can mark payslips as paid.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payslip = self.get_object()
        
        if payslip.status != 'APPROVED':
            return Response(
                {'detail': 'Payslip must be approved before marking as paid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payslip.status = 'PAID'
        payslip.payment_date = request.data.get('payment_date', timezone.now().date())
        payslip.payment_mode = request.data.get('payment_mode', 'Bank Transfer')
        payslip.payment_reference = request.data.get('payment_reference', '')
        payslip.save()
        
        serializer = self.get_serializer(payslip)
        return Response({
            'message': 'Payslip marked as paid',
            'payslip': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download payslip as PDF"""
        payslip = self.get_object()
        
        # Check permission: Admin/HR or owner
        if request.user.role not in ['admin', 'hr']:
            if payslip.employee.user != request.user:
                return Response(
                    {'detail': 'You can only download your own payslips.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Generate simple text-based payslip (PDF generation requires additional library)
        content = self._generate_payslip_content(payslip)
        
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="payslip_{payslip.employee.employee_id}_{payslip.month}_{payslip.year}.txt"'
        return response
    
    def _generate_payslip_content(self, payslip):
        """Generate payslip content"""
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        content = f"""
================================================================================
                              PAYSLIP
================================================================================

Employee ID: {payslip.employee.employee_id}
Employee Name: {payslip.employee.user.get_full_name()}
Designation: {payslip.employee.designation}
Department: {payslip.employee.department}

Month: {months[payslip.month]} {payslip.year}
Working Days: {payslip.total_working_days}
Days Worked: {payslip.days_worked}
Days Absent: {payslip.days_absent}

================================================================================
                              EARNINGS
================================================================================
Basic Salary:                  {payslip.basic_salary:>12.2f}
HRA:                          {payslip.hra:>12.2f}
Transport Allowance:          {payslip.transport_allowance:>12.2f}
Medical Allowance:            {payslip.medical_allowance:>12.2f}
Special Allowance:            {payslip.special_allowance:>12.2f}
Bonus:                        {payslip.bonus:>12.2f}
Overtime Pay:                 {payslip.overtime_pay:>12.2f}
Incentives:                   {payslip.incentives:>12.2f}
                              _______________
GROSS SALARY:                 {payslip.gross_salary:>12.2f}

================================================================================
                              DEDUCTIONS
================================================================================
PF (Employee):                {payslip.pf_employee:>12.2f}
ESI (Employee):               {payslip.esi_employee:>12.2f}
Professional Tax:             {payslip.professional_tax:>12.2f}
TDS:                          {payslip.tds:>12.2f}
Loan Deduction:               {payslip.loan_deduction:>12.2f}
Other Deductions:             {payslip.other_deductions:>12.2f}
                              _______________
TOTAL DEDUCTIONS:             {payslip.total_deductions:>12.2f}

================================================================================
NET SALARY:                   {payslip.net_salary:>12.2f}
================================================================================

Status: {payslip.status}
Generated On: {payslip.generated_at.strftime('%Y-%m-%d')}
{f"Approved By: {payslip.approved_by.email}" if payslip.approved_by else ""}
{f"Payment Date: {payslip.payment_date}" if payslip.payment_date else ""}

This is a computer-generated payslip and does not require a signature.
================================================================================
"""
        return content


class SalaryHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for salary history tracking
    """
    serializer_class = SalaryHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter by employee parameter (for admin/HR filtering)
        employee_id = self.request.query_params.get('employee', None)
        
        # Admin/HR can see all history or filter by specific employee
        if user.role in ['admin', 'hr']:
            if employee_id:
                # Admin/HR filtering by specific employee (can be User ID or EmployeeProfile ID)
                try:
                    employee_profile = EmployeeProfile.objects.get(id=employee_id)
                    queryset = SalaryHistory.objects.filter(employee=employee_profile)
                except EmployeeProfile.DoesNotExist:
                    # Assume it's a User ID, try to find the profile
                    try:
                        employee_profile = EmployeeProfile.objects.get(user_id=employee_id)
                        queryset = SalaryHistory.objects.filter(employee=employee_profile)
                    except EmployeeProfile.DoesNotExist:
                        # No profile found for this user, return empty queryset
                        queryset = SalaryHistory.objects.none()
            else:
                queryset = SalaryHistory.objects.all()
        else:
            # Employees can see only their own history (ignore employee parameter)
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                queryset = SalaryHistory.objects.filter(employee=employee_profile)
            except EmployeeProfile.DoesNotExist:
                queryset = SalaryHistory.objects.none()
        
        return queryset.select_related('employee', 'approved_by', 'created_by')
    
    def create(self, request, *args, **kwargs):
        """Create salary history record - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can create salary history records.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DeductionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing additional deductions
    """
    serializer_class = DeductionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter by employee parameter (for admin/HR filtering)
        employee_id = self.request.query_params.get('employee', None)
        
        # Admin/HR can see all deductions or filter by specific employee
        if user.role in ['admin', 'hr']:
            if employee_id:
                # Admin/HR filtering by specific employee (can be User ID or EmployeeProfile ID)
                try:
                    employee_profile = EmployeeProfile.objects.get(id=employee_id)
                    queryset = Deduction.objects.filter(employee=employee_profile)
                except EmployeeProfile.DoesNotExist:
                    # Assume it's a User ID, try to find the profile
                    try:
                        employee_profile = EmployeeProfile.objects.get(user_id=employee_id)
                        queryset = Deduction.objects.filter(employee=employee_profile)
                    except EmployeeProfile.DoesNotExist:
                        # No profile found for this user, return empty queryset
                        queryset = Deduction.objects.none()
            else:
                queryset = Deduction.objects.all()
        else:
            # Employees can see only their own deductions (ignore employee parameter)
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                queryset = Deduction.objects.filter(employee=employee_profile)
            except EmployeeProfile.DoesNotExist:
                queryset = Deduction.objects.none()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.select_related('employee', 'created_by')
    
    def create(self, request, *args, **kwargs):
        """Create deduction - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can create deductions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle employee field - can be User ID or EmployeeProfile ID
        data = request.data.copy()
        employee_value = data.get('employee')
        
        if employee_value:
            # Try to find EmployeeProfile
            try:
                # First try as EmployeeProfile ID
                employee_profile = EmployeeProfile.objects.get(id=employee_value)
                data['employee'] = employee_profile.id
            except (EmployeeProfile.DoesNotExist, ValueError):
                # Try as User ID
                try:
                    employee_profile = EmployeeProfile.objects.get(user_id=employee_value)
                    data['employee'] = employee_profile.id
                except EmployeeProfile.DoesNotExist:
                    return Response(
                        {'detail': f'No employee profile found for the provided ID: {employee_value}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update deduction - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can update deductions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
