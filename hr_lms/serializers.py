"""
Serializers for Learning Management System (LMS)
"""

from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    Course, Module, Enrollment, ModuleProgress,
    Quiz, QuizQuestion, QuizAttempt, Certificate, Skill, UserSkill
)

User = get_user_model()


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for Module model"""
    
    class Meta:
        model = Module
        fields = [
            'id', 'course', 'title', 'description', 'content_type', 'order',
            'content', 'video_url', 'document', 'duration_minutes',
            'is_mandatory', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing modules"""
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'content_type', 'order', 'duration_minutes',
            'is_mandatory', 'is_published'
        ]


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for listing courses"""
    
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    total_modules = serializers.IntegerField(read_only=True)
    total_enrollments = serializers.IntegerField(read_only=True)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'category', 'level', 'instructor',
            'instructor_name', 'duration_hours', 'thumbnail', 'is_mandatory',
            'status', 'start_date', 'end_date', 'total_modules', 'total_enrollments',
            'completion_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'instructor_name', 'total_modules', 
                           'total_enrollments', 'completion_rate']


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for course with modules"""
    
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    modules = ModuleListSerializer(many=True, read_only=True)
    total_modules = serializers.IntegerField(read_only=True)
    total_enrollments = serializers.IntegerField(read_only=True)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'category', 'level', 'instructor',
            'instructor_name', 'duration_hours', 'thumbnail', 'is_mandatory',
            'prerequisites', 'learning_objectives', 'status', 'max_enrollments',
            'enrollment_deadline', 'start_date', 'end_date', 'modules',
            'total_modules', 'total_enrollments', 'completion_rate', 'is_full',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'instructor_name',
                           'modules', 'total_modules', 'total_enrollments',
                           'completion_rate', 'is_full', 'created_by_name']


class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating courses"""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'category', 'level', 'instructor',
            'duration_hours', 'thumbnail', 'is_mandatory', 'prerequisites',
            'learning_objectives', 'status', 'max_enrollments',
            'enrollment_deadline', 'start_date', 'end_date'
        ]
    
    def validate(self, data):
        """Validate course data"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
        
        if data.get('enrollment_deadline') and data.get('start_date'):
            if data['enrollment_deadline'] > data['start_date']:
                raise serializers.ValidationError({
                    'enrollment_deadline': 'Enrollment deadline must be before start date'
                })
        
        return data
    
    def create(self, validated_data):
        """Create course with creator"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ModuleProgressSerializer(serializers.ModelSerializer):
    """Serializer for module progress"""
    
    module_title = serializers.CharField(source='module.title', read_only=True)
    module_content_type = serializers.CharField(source='module.content_type', read_only=True)
    module_duration = serializers.IntegerField(source='module.duration_minutes', read_only=True)
    
    class Meta:
        model = ModuleProgress
        fields = [
            'id', 'enrollment', 'module', 'module_title', 'module_content_type',
            'module_duration', 'status', 'started_at', 'completed_at',
            'time_spent_minutes', 'last_position', 'attempts', 'updated_at'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'updated_at',
                           'module_title', 'module_content_type', 'module_duration']


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing enrollments"""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_category = serializers.CharField(source='course.category', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    time_spent_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_title', 'course_category', 'user',
            'user_name', 'status', 'enrolled_at', 'started_at', 'completed_at',
            'deadline', 'progress_percentage', 'modules_completed', 'final_score',
            'is_overdue', 'time_spent_days'
        ]
        read_only_fields = ['id', 'enrolled_at', 'course_title', 'course_category',
                           'user_name', 'is_overdue', 'time_spent_days']


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for enrollment with progress"""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_description = serializers.CharField(source='course.description', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    module_progress = ModuleProgressSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    time_spent_days = serializers.IntegerField(read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_title', 'course_description', 'user',
            'user_name', 'status', 'enrolled_at', 'started_at', 'completed_at',
            'deadline', 'progress_percentage', 'modules_completed', 'final_score',
            'approved_by', 'approved_by_name', 'approved_at', 'module_progress',
            'is_overdue', 'time_spent_days', 'updated_at'
        ]
        read_only_fields = ['id', 'enrolled_at', 'updated_at', 'course_title',
                           'course_description', 'user_name', 'module_progress',
                           'is_overdue', 'time_spent_days', 'approved_by_name']


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating enrollment"""
    
    class Meta:
        model = Enrollment
        fields = ['course', 'deadline']
    
    def validate_course(self, value):
        """Validate course enrollment"""
        user = self.context['request'].user
        
        # Check if already enrolled (excluding dropped enrollments)
        existing_enrollment = Enrollment.objects.filter(course=value, user=user).first()
        if existing_enrollment:
            if existing_enrollment.status in ['active', 'pending', 'completed']:
                raise serializers.ValidationError("You are already enrolled in this course")
            # If dropped, we'll reactivate it in the create method
        
        # Check if course is published
        if value.status != 'published':
            raise serializers.ValidationError("This course is not available for enrollment")
        
        # Check if course is full
        if value.is_full:
            raise serializers.ValidationError("This course has reached maximum enrollment")
        
        # Check enrollment deadline
        if value.enrollment_deadline and timezone.now().date() > value.enrollment_deadline:
            raise serializers.ValidationError("Enrollment deadline has passed")
        
        return value
    
    def create(self, validated_data):
        """Create enrollment and module progress records"""
        user = self.context['request'].user
        course = validated_data['course']
        
        # Check if there's a dropped enrollment to reactivate
        existing_enrollment = Enrollment.objects.filter(course=course, user=user, status='dropped').first()
        
        if existing_enrollment:
            # Reactivate dropped enrollment
            existing_enrollment.status = 'pending' if course.is_mandatory else 'active'
            existing_enrollment.deadline = validated_data.get('deadline', existing_enrollment.deadline)
            existing_enrollment.enrolled_at = timezone.now()
            existing_enrollment.started_at = None
            existing_enrollment.completed_at = None
            existing_enrollment.final_score = None
            existing_enrollment.save()
            
            # Reset or create module progress records
            modules = course.modules.filter(is_published=True)
            for module in modules:
                progress, created = ModuleProgress.objects.get_or_create(
                    enrollment=existing_enrollment,
                    module=module,
                    defaults={'status': 'not_started'}
                )
                if not created:
                    # Reset existing progress
                    progress.status = 'not_started'
                    progress.started_at = None
                    progress.completed_at = None
                    progress.time_spent_minutes = 0
                    progress.last_position = ''
                    progress.attempts = 0
                    progress.save()
            
            return existing_enrollment
        
        # Create new enrollment
        validated_data['user'] = user
        
        # Set status based on course requirements
        if course.is_mandatory:
            validated_data['status'] = 'pending'
        else:
            validated_data['status'] = 'active'
        
        enrollment = super().create(validated_data)
        
        # Create module progress for all modules
        modules = enrollment.course.modules.filter(is_published=True)
        for module in modules:
            ModuleProgress.objects.create(
                enrollment=enrollment,
                module=module,
                status='not_started'
            )
        
        return enrollment


class UpdateProgressSerializer(serializers.Serializer):
    """Serializer for updating module progress"""
    
    module_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['in_progress', 'completed'])
    time_spent_minutes = serializers.IntegerField(min_value=0, required=False)
    last_position = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_module_id(self, value):
        """Validate module exists"""
        if not Module.objects.filter(id=value).exists():
            raise serializers.ValidationError("Module not found")
        return value


# ============================================================================
# DAY 21 SERIALIZERS - Quiz, Certificate, Skills
# ============================================================================

class QuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer for Quiz Questions"""
    
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'quiz', 'question_text', 'question_type', 'points',
            'order', 'options', 'correct_answer', 'explanation',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'correct_answer': {'write_only': True}  # Don't expose correct answers in list
        }


class QuizQuestionPublicSerializer(serializers.ModelSerializer):
    """Public serializer without correct answers"""
    
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'question_text', 'question_type', 'points',
            'order', 'options'
        ]


class QuizListSerializer(serializers.ModelSerializer):
    """Serializer for listing quizzes"""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True, allow_null=True)
    total_questions = serializers.IntegerField(read_only=True)
    total_points = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'course', 'course_title', 'module', 'module_title',
            'title', 'description', 'difficulty', 'time_limit_minutes',
            'passing_score', 'max_attempts', 'is_mandatory',
            'total_questions', 'total_points', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class QuizDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for quiz with questions"""
    
    questions = QuizQuestionPublicSerializer(many=True, read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True, allow_null=True)
    total_questions = serializers.IntegerField(read_only=True)
    total_points = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'course', 'course_title', 'module', 'module_title',
            'title', 'description', 'difficulty', 'time_limit_minutes',
            'passing_score', 'max_attempts', 'is_mandatory',
            'randomize_questions', 'show_correct_answers',
            'questions', 'total_questions', 'total_points',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuizAttemptListSerializer(serializers.ModelSerializer):
    """Serializer for listing quiz attempts"""
    
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'user', 'user_name',
            'attempt_number', 'status', 'score', 'points_earned',
            'total_points', 'passed', 'started_at', 'submitted_at',
            'time_taken_minutes'
        ]
        read_only_fields = [
            'id', 'started_at', 'score', 'points_earned', 
            'total_points', 'passed'
        ]


class QuizAttemptDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for quiz attempt with answers"""
    
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    quiz_details = QuizDetailSerializer(source='quiz', read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'quiz_details', 'user', 'user_name',
            'attempt_number', 'status', 'score', 'points_earned',
            'total_points', 'passed', 'started_at', 'submitted_at',
            'time_taken_minutes', 'answers'
        ]
        read_only_fields = [
            'id', 'started_at', 'score', 'points_earned',
            'total_points', 'passed'
        ]


class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers"""
    
    answers = serializers.JSONField()
    
    def validate_answers(self, value):
        """Validate answers format"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Answers must be a dictionary")
        
        # Validate each answer has required fields
        for question_id, answer_data in value.items():
            if not isinstance(answer_data, dict):
                raise serializers.ValidationError(f"Answer for question {question_id} must be a dictionary")
            
            if 'answer' not in answer_data:
                raise serializers.ValidationError(f"Answer for question {question_id} missing 'answer' field")
        
        return value


class CertificateListSerializer(serializers.ModelSerializer):
    """Serializer for listing certificates"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.get_full_name', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'user', 'user_name', 'course',
            'course_title', 'title', 'issued_date', 'expiry_date',
            'status', 'completion_score', 'quiz_average', 'is_valid',
            'issued_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'certificate_id', 'issued_date', 'created_at', 'is_valid'
        ]


class CertificateDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for certificate"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_description = serializers.CharField(source='course.description', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.get_full_name', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'user', 'user_name', 'user_email',
            'course', 'course_title', 'course_description', 'enrollment',
            'title', 'description', 'issued_date', 'expiry_date',
            'status', 'completion_score', 'quiz_average',
            'certificate_file', 'verification_url', 'is_valid',
            'issued_by', 'issued_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'certificate_id', 'issued_date', 'created_at',
            'updated_at', 'is_valid'
        ]


class CertificateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating certificates"""
    
    title = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Certificate
        fields = [
            'user', 'course', 'enrollment', 'title', 'description',
            'expiry_date', 'completion_score', 'quiz_average'
        ]
    
    def validate(self, data):
        """Validate certificate creation"""
        user = data.get('user')
        course = data.get('course')
        
        # Check if certificate already exists
        if Certificate.objects.filter(user=user, course=course).exists():
            raise serializers.ValidationError(
                "Certificate already exists for this user and course"
            )
        
        # Check if enrollment exists and is completed
        enrollment = data.get('enrollment')
        if enrollment:
            if enrollment.user != user or enrollment.course != course:
                raise serializers.ValidationError(
                    "Enrollment must belong to the same user and course"
                )
            
            if enrollment.status != 'completed':
                raise serializers.ValidationError(
                    "Certificate can only be issued for completed enrollments"
                )
        
        return data
    
    def create(self, validated_data):
        """Create certificate with auto-generated title if not provided"""
        if not validated_data.get('title'):
            course = validated_data['course']
            validated_data['title'] = f"Certificate of Completion - {course.title}"
        
        if not validated_data.get('description'):
            course = validated_data['course']
            user = validated_data['user']
            validated_data['description'] = (
                f"This certifies that {user.get_full_name()} has successfully "
                f"completed the course '{course.title}'"
            )
        
        return super().create(validated_data)


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skills"""
    
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Skill
        fields = [
            'id', 'name', 'description', 'category',
            'courses_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_courses_count(self, obj):
        return obj.courses.count()


class UserSkillListSerializer(serializers.ModelSerializer):
    """Serializer for listing user skills"""
    
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_category = serializers.CharField(source='skill.get_category_display', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    
    class Meta:
        model = UserSkill
        fields = [
            'id', 'skill', 'skill_name', 'skill_category',
            'proficiency_level', 'source', 'course', 'course_title',
            'endorsement_count', 'acquired_date', 'last_used_date'
        ]
        read_only_fields = ['id', 'acquired_date']


class UserSkillDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user skill"""
    
    skill_details = SkillSerializer(source='skill', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    certificate_id = serializers.CharField(source='certificate.certificate_id', read_only=True, allow_null=True)
    
    class Meta:
        model = UserSkill
        fields = [
            'id', 'user', 'user_name', 'skill', 'skill_details',
            'proficiency_level', 'source', 'course', 'course_title',
            'certificate', 'certificate_id', 'endorsement_count',
            'acquired_date', 'last_used_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'acquired_date', 'created_at', 'updated_at']


class UserSkillCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user skills"""
    
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = UserSkill
        fields = [
            'user', 'skill', 'proficiency_level', 'source',
            'course', 'certificate', 'last_used_date'
        ]
    
    def validate(self, data):
        """Validate user skill creation"""
        user = data.get('user')
        skill = data.get('skill')
        
        # Skip duplicate check if user not provided (will be set in perform_create)
        if not user:
            return data
        
        # Check if skill already exists for user
        if UserSkill.objects.filter(user=user, skill=skill).exists():
            raise serializers.ValidationError(
                "This skill already exists for the user. Use update instead."
            )
        
        return data
