"""
Views for Learning Management System (LMS)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Avg
from authentication.permissions import IsAdminOrHR, IsManagerOrAbove
from authentication.models import User

from .models import (
    Course, Module, Enrollment, ModuleProgress,
    Quiz, QuizQuestion, QuizAttempt, Certificate, Skill, UserSkill
)
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateSerializer,
    ModuleSerializer, ModuleListSerializer,
    EnrollmentListSerializer, EnrollmentDetailSerializer, EnrollmentCreateSerializer,
    ModuleProgressSerializer, UpdateProgressSerializer,
    # Day 21 serializers
    QuizListSerializer, QuizDetailSerializer, QuizQuestionSerializer,
    QuizAttemptListSerializer, QuizAttemptDetailSerializer, QuizSubmissionSerializer,
    CertificateListSerializer, CertificateDetailSerializer, CertificateCreateSerializer,
    SkillSerializer, UserSkillListSerializer, UserSkillDetailSerializer, UserSkillCreateSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course management
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin/HR only
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get courses based on user role"""
        user = self.request.user
        queryset = Course.objects.all()
        
        # Filter by status
        if user.role in ['admin', 'hr']:
            # Admin/HR can see all courses
            pass
        else:
            # Others see only published courses
            queryset = queryset.filter(status='published')
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by level
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)
        
        # Filter by mandatory
        is_mandatory = self.request.query_params.get('is_mandatory', None)
        if is_mandatory is not None:
            queryset = queryset.filter(is_mandatory=is_mandatory.lower() == 'true')
        
        # Search by title
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateSerializer
        return CourseDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrHR()]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """Get all modules for a course"""
        course = self.get_object()
        modules = course.modules.filter(is_published=True)
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrHR])
    def publish(self, request, pk=None):
        """Publish a course"""
        course = self.get_object()
        
        if course.status == 'published':
            return Response(
                {'detail': 'Course is already published'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        course.status = 'published'
        course.save()
        
        return Response({'detail': 'Course published successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrHR])
    def archive(self, request, pk=None):
        """Archive a course"""
        course = self.get_object()
        course.status = 'archived'
        course.save()
        
        return Response({'detail': 'Course archived successfully'})
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get course statistics"""
        course = self.get_object()
        
        enrollments = course.enrollments.all()
        
        stats = {
            'total_enrollments': enrollments.count(),
            'active_enrollments': enrollments.filter(status='active').count(),
            'completed_enrollments': enrollments.filter(status='completed').count(),
            'pending_enrollments': enrollments.filter(status='pending').count(),
            'average_progress': enrollments.aggregate(
                avg=Avg('progress_percentage')
            )['avg'] or 0,
            'completion_rate': course.completion_rate,
            'total_modules': course.total_modules,
        }
        
        return Response(stats)


class ModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Module management
    
    Permissions:
    - List/Retrieve: Enrolled users or Admin/HR
    - Create/Update/Delete: Admin/HR only
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = ModuleSerializer
    
    def get_queryset(self):
        """Get modules based on user role and enrollment"""
        user = self.request.user
        queryset = Module.objects.all()
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Non-admin users see only published modules
        if user.role not in ['admin', 'hr']:
            queryset = queryset.filter(is_published=True)
        
        return queryset
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrHR()]
        return super().get_permissions()


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Enrollment management
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get enrollments based on user role"""
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            # Admin/HR see all enrollments
            queryset = Enrollment.objects.all()
        elif user.role == 'manager':
            # Managers see their team's enrollments
            team_users = User.objects.filter(manager=user)
            queryset = Enrollment.objects.filter(
                Q(user=user) | Q(user__in=team_users)
            )
        else:
            # Employees see only their own
            queryset = Enrollment.objects.filter(user=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.select_related('course', 'user', 'approved_by')
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return EnrollmentCreateSerializer
        elif self.action == 'list':
            return EnrollmentListSerializer
        return EnrollmentDetailSerializer
    
    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """Enroll in a course"""
        serializer = EnrollmentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()
        
        return Response(
            EnrollmentDetailSerializer(enrollment).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAbove])
    def approve(self, request, pk=None):
        """Approve enrollment (for mandatory courses)"""
        enrollment = self.get_object()
        
        if enrollment.status != 'pending':
            return Response(
                {'detail': 'Only pending enrollments can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment.status = 'active'
        enrollment.approved_by = request.user
        enrollment.approved_at = timezone.now()
        enrollment.save()
        
        return Response({'detail': 'Enrollment approved successfully'})
    
    @action(detail=True, methods=['post'])
    def drop(self, request, pk=None):
        """Drop from course"""
        enrollment = self.get_object()
        
        # Only the enrolled user or admin/HR can drop
        if enrollment.user != request.user and request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'You do not have permission to drop this enrollment'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if enrollment.status == 'completed':
            return Response(
                {'detail': 'Cannot drop completed course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment.status = 'dropped'
        enrollment.save()
        
        return Response({'detail': 'Successfully dropped from course'})
    
    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """Get current user's enrollments (excluding dropped)"""
        enrollments = Enrollment.objects.filter(user=request.user).exclude(status='dropped')
        serializer = EnrollmentListSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending enrollments (for managers/admin)"""
        user = request.user
        
        if user.role in ['admin', 'hr']:
            enrollments = Enrollment.objects.filter(status='pending')
        elif user.role == 'manager':
            team_users = User.objects.filter(manager=user)
            enrollments = Enrollment.objects.filter(
                status='pending',
                user__in=team_users
            )
        else:
            return Response(
                {'detail': 'You do not have permission to view pending enrollments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EnrollmentListSerializer(enrollments, many=True)
        return Response(serializer.data)


class ModuleProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Module Progress tracking
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = ModuleProgressSerializer
    
    def get_queryset(self):
        """Get progress based on user"""
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            queryset = ModuleProgress.objects.all()
        else:
            # Users see only their own progress
            queryset = ModuleProgress.objects.filter(enrollment__user=user)
        
        # Filter by enrollment
        enrollment_id = self.request.query_params.get('enrollment', None)
        if enrollment_id:
            queryset = queryset.filter(enrollment_id=enrollment_id)
        
        return queryset.select_related('enrollment', 'module')
    
    @action(detail=False, methods=['post'])
    def update_progress(self, request):
        """Update module progress"""
        serializer = UpdateProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        module_id = serializer.validated_data['module_id']
        progress_status = serializer.validated_data['status']
        
        # Get the module progress
        try:
            progress = ModuleProgress.objects.get(
                module_id=module_id,
                enrollment__user=request.user
            )
        except ModuleProgress.DoesNotExist:
            return Response(
                {'detail': 'Module progress not found. Ensure you are enrolled in the course.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update progress
        if progress_status == 'in_progress':
            progress.mark_started()
        elif progress_status == 'completed':
            progress.mark_completed()
        
        # Update time spent if provided
        if 'time_spent_minutes' in serializer.validated_data:
            progress.time_spent_minutes += serializer.validated_data['time_spent_minutes']
        
        # Update last position if provided
        if 'last_position' in serializer.validated_data:
            progress.last_position = serializer.validated_data['last_position']
        
        progress.save()
        
        return Response(ModuleProgressSerializer(progress).data)
    
    @action(detail=False, methods=['get'])
    def my_progress(self, request):
        """Get current user's progress across all courses"""
        enrollment_id = request.query_params.get('enrollment', None)
        
        if enrollment_id:
            progress = ModuleProgress.objects.filter(
                enrollment_id=enrollment_id,
                enrollment__user=request.user
            )
        else:
            progress = ModuleProgress.objects.filter(enrollment__user=request.user)
        
        serializer = ModuleProgressSerializer(progress, many=True)
        return Response(serializer.data)


# ============================================================================
# DAY 21 VIEWSETS - Quiz, Certificate, Skills
# ============================================================================

class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quiz management
    
    Permissions:
    - List/Retrieve: All authenticated users (enrolled students see published quizzes)
    - Create/Update/Delete: Admin/HR and course instructors
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get quizzes based on user role"""
        user = self.request.user
        queryset = Quiz.objects.all()
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter by module
        module_id = self.request.query_params.get('module', None)
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'retrieve':
            return QuizDetailSerializer
        return QuizListSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrHR()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Set created_by when creating quiz"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_attempt(self, request, pk=None):
        """Start a new quiz attempt"""
        quiz = self.get_object()
        user = request.user
        
        # Check if user has enrollment for this course
        enrollment = Enrollment.objects.filter(
            user=user,
            course=quiz.course,
            status='active'
        ).first()
        
        if not enrollment:
            return Response(
                {'error': 'You must be enrolled in the course to take this quiz'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check attempt limit
        attempts_count = QuizAttempt.objects.filter(
            quiz=quiz,
            user=user
        ).count()
        
        if attempts_count >= quiz.max_attempts:
            return Response(
                {'error': f'Maximum attempts ({quiz.max_attempts}) reached'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=user,
            enrollment=enrollment,
            attempt_number=attempts_count + 1,
            total_points=quiz.total_points,
            status='in_progress'
        )
        
        serializer = QuizAttemptDetailSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit quiz answers"""
        quiz = self.get_object()
        user = request.user
        
        # Get the in-progress attempt
        attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=user,
            status='in_progress'
        ).order_by('-started_at').first()
        
        if not attempt:
            return Response(
                {'error': 'No active quiz attempt found. Start a new attempt first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate submission
        submission_serializer = QuizSubmissionSerializer(data=request.data)
        if not submission_serializer.is_valid():
            return Response(
                submission_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        answers = submission_serializer.validated_data['answers']
        
        # Grade the quiz
        graded_answers = {}
        questions = quiz.questions.all()
        
        for question in questions:
            question_id = str(question.id)
            user_answer = answers.get(question_id, {}).get('answer', [])
            correct_answer = question.correct_answer
            
            # Check if answer is correct
            is_correct = False
            if question.question_type in ['single_choice', 'multiple_choice', 'true_false']:
                # Compare arrays (case-insensitive for text)
                user_set = set([str(a).lower() for a in user_answer])
                correct_set = set([str(a).lower() for a in correct_answer])
                is_correct = user_set == correct_set
            elif question.question_type == 'text':
                # For text, check if any correct answer matches
                is_correct = any(
                    str(user_answer).lower().strip() == str(ans).lower().strip()
                    for ans in correct_answer
                )
            
            # Calculate points
            points = float(question.points) if is_correct else 0
            
            graded_answers[question_id] = {
                'answer': user_answer,
                'is_correct': is_correct,
                'points': points,
                'correct_answer': correct_answer if quiz.show_correct_answers else None,
                'explanation': question.explanation if quiz.show_correct_answers else None
            }
        
        # Update attempt
        attempt.answers = graded_answers
        attempt.status = 'graded'
        attempt.submitted_at = timezone.now()
        
        # Calculate time taken
        time_delta = attempt.submitted_at - attempt.started_at
        attempt.time_taken_minutes = round(time_delta.total_seconds() / 60, 2)
        
        # Calculate score
        attempt.calculate_score()
        
        serializer = QuizAttemptDetailSerializer(attempt)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_attempts(self, request):
        """Get current user's quiz attempts"""
        attempts = QuizAttempt.objects.filter(user=request.user)
        
        # Filter by quiz
        quiz_id = request.query_params.get('quiz', None)
        if quiz_id:
            attempts = attempts.filter(quiz_id=quiz_id)
        
        serializer = QuizAttemptListSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """Get quiz leaderboard (best scores)"""
        quiz = self.get_object()
        
        # Get best attempt for each user
        from django.db.models import Max
        
        best_attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            status='graded',
            passed=True
        ).values('user').annotate(
            best_score=Max('score')
        ).order_by('-best_score')[:10]
        
        # Get full attempt details
        leaderboard = []
        for item in best_attempts:
            attempt = QuizAttempt.objects.filter(
                quiz=quiz,
                user_id=item['user'],
                score=item['best_score']
            ).first()
            
            if attempt:
                leaderboard.append({
                    'user_id': attempt.user.id,
                    'user_name': attempt.user.get_full_name(),
                    'score': float(attempt.score),
                    'time_taken': float(attempt.time_taken_minutes) if attempt.time_taken_minutes else None,
                    'submitted_at': attempt.submitted_at
                })
        
        return Response(leaderboard)


class QuizQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quiz Questions management
    
    All authenticated users can view questions (for taking quizzes)
    Only Admin/HR can create/update/delete questions
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = QuizQuestionSerializer
    
    def get_queryset(self):
        """Get questions, optionally filtered by quiz"""
        queryset = QuizQuestion.objects.all()
        
        quiz_id = self.request.query_params.get('quiz', None)
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id)
        
        return queryset
    
    def get_permissions(self):
        """
        Admin/HR only for create, update, delete
        All authenticated users can view (list, retrieve)
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrHR()]
        return [IsAuthenticated()]


class CertificateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Certificate management
    
    Permissions:
    - List/Retrieve: Users can see their own certificates, Admin/HR see all
    - Create: Admin/HR only (auto-generated on course completion)
    - Update/Delete: Admin/HR only
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get certificates based on user role"""
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            queryset = Certificate.objects.all()
        else:
            queryset = Certificate.objects.filter(user=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return CertificateCreateSerializer
        elif self.action == 'retrieve':
            return CertificateDetailSerializer
        return CertificateListSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrHR()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Set issued_by when creating certificate"""
        serializer.save(issued_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        """Verify certificate authenticity"""
        certificate = self.get_object()
        
        return Response({
            'certificate_id': certificate.certificate_id,
            'user_name': certificate.user.get_full_name(),
            'user_email': certificate.user.email,
            'course_title': certificate.course.title,
            'issued_date': certificate.issued_date,
            'expiry_date': certificate.expiry_date,
            'status': certificate.status,
            'is_valid': certificate.is_valid,
            'completion_score': certificate.completion_score,
            'verification_url': certificate.verification_url
        })
    
    @action(detail=False, methods=['get'])
    def my_certificates(self, request):
        """Get current user's certificates"""
        certificates = Certificate.objects.filter(user=request.user)
        serializer = CertificateListSerializer(certificates, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke a certificate"""
        certificate = self.get_object()
        
        if certificate.status == 'revoked':
            return Response(
                {'error': 'Certificate is already revoked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificate.status = 'revoked'
        certificate.save()
        
        return Response({'message': 'Certificate revoked successfully'})
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a revoked certificate"""
        certificate = self.get_object()
        
        if certificate.status != 'revoked':
            return Response(
                {'error': 'Only revoked certificates can be reactivated'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificate.status = 'active'
        certificate.save()
        
        return Response({'message': 'Certificate reactivated successfully'})


class SkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Skill management
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: Admin/HR only
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = SkillSerializer
    
    def get_queryset(self):
        """Get skills, optionally filtered"""
        queryset = Skill.objects.all()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrHR()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def users_with_skill(self, request, pk=None):
        """Get users who have this skill"""
        skill = self.get_object()
        
        user_skills = UserSkill.objects.filter(skill=skill).select_related('user')
        
        data = [
            {
                'user_id': us.user.id,
                'user_name': us.user.get_full_name(),
                'proficiency_level': us.proficiency_level,
                'acquired_date': us.acquired_date,
                'endorsement_count': us.endorsement_count
            }
            for us in user_skills
        ]
        
        return Response(data)


class UserSkillViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserSkill management
    
    Permissions:
    - List/Retrieve: Users see their own skills, managers see team, admin/HR see all
    - Create: Auto-created on course completion, manual by admin/HR
    - Update: User can update last_used_date, admin/HR can update all
    - Delete: Admin/HR only
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get user skills based on role"""
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            queryset = UserSkill.objects.all()
        elif user.role == 'manager':
            # Managers see their team's skills
            team_members = User.objects.filter(manager=user)
            queryset = UserSkill.objects.filter(
                Q(user=user) | Q(user__in=team_members)
            )
        else:
            queryset = UserSkill.objects.filter(user=user)
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by skill category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(skill__category=category)
        
        # Filter by proficiency level
        proficiency = self.request.query_params.get('proficiency', None)
        if proficiency:
            queryset = queryset.filter(proficiency_level=proficiency)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return UserSkillCreateSerializer
        elif self.action == 'retrieve':
            return UserSkillDetailSerializer
        return UserSkillListSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        # All authenticated users can create and delete their own skills
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Auto-set user to current user if not provided"""
        if not serializer.validated_data.get('user'):
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    def perform_destroy(self, instance):
        """Only allow users to delete their own skills, or admin/HR to delete any"""
        user = self.request.user
        if user.role not in ['admin', 'hr'] and instance.user != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own skills.")
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def my_skills(self, request):
        """Get current user's skills"""
        skills = UserSkill.objects.filter(user=request.user)
        serializer = UserSkillListSerializer(skills, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def endorse(self, request, pk=None):
        """Endorse a user's skill"""
        user_skill = self.get_object()
        
        # Users cannot endorse their own skills
        if user_skill.user == request.user:
            return Response(
                {'error': 'You cannot endorse your own skills'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Increment endorsement count
        user_skill.endorsement_count += 1
        user_skill.save()
        
        return Response({
            'message': 'Skill endorsed successfully',
            'endorsement_count': user_skill.endorsement_count
        })
    
    @action(detail=False, methods=['get'])
    def skill_gap_analysis(self, request):
        """Analyze skill gaps for current user or team"""
        user = request.user
        
        # Get target user (self or team member)
        target_user_id = request.query_params.get('user', None)
        if target_user_id:
            # Check permission
            if user.role not in ['admin', 'hr', 'manager']:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            target_user = User.objects.get(id=target_user_id)
        else:
            target_user = user
        
        # Get user's current skills
        current_skills = set(
            UserSkill.objects.filter(user=target_user).values_list('skill_id', flat=True)
        )
        
        # Get all skills from mandatory courses
        mandatory_courses = Course.objects.filter(is_mandatory=True, status='published')
        recommended_skills = Skill.objects.filter(
            courses__in=mandatory_courses
        ).distinct().exclude(id__in=current_skills)
        
        skill_serializer = SkillSerializer(recommended_skills, many=True)
        
        return Response({
            'user_id': target_user.id,
            'user_name': target_user.get_full_name(),
            'current_skills_count': len(current_skills),
            'recommended_skills': skill_serializer.data
        })
