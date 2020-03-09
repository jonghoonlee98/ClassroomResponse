from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

from ..decorators import student_required
from ..forms import StudentInterestsForm, StudentSignUpForm, TakeQuizForm, CourseRegistrationForm, PasswordResetRequestForm, SetPasswordForm
from ..models import *
from ..parse_data import *

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template import loader
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from classroom_response.settings import DEFAULT_FROM_EMAIL
from django.views.generic import *
from django.contrib import messages
from classroom.models import User

import json


class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('students:course_list')

class StudentResetPasswordRequestView(FormView):
    template_name = "registration/forgot_template.html"
    success_url = 'classroom/accounts/login.html'
    form_class = PasswordResetRequestForm

    @staticmethod
    def validate_email_address(email):
        try: 
            validate_email(email)
            return True
        except ValidationError:
            return False

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            data= form.cleaned_data["email_or_username"]
        if self.validate_email_address(data) is True:
            associated_users = User.objects.filter(email=data)
            if associated_users.exists():
                for user in associated_users:
                        c = {
                            'email': user.email,
                            'domain': request.META['HTTP_HOST'],
                            'site_name': 'classroomresponsesystem.herokuapp.com',
                            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                            'user': user,
                            'token': default_token_generator.make_token(user),
                            'protocol': 'http',
                            }
                        subject_template_name='registration/password_reset_subject.txt'
                        # copied from django/contrib/admin/templates/registration/password_reset_subject.txt to templates directory
                        email_template_name='registration/password_reset_email.html'
                        # copied from django/contrib/admin/templates/registration/password_reset_email.html to templates directory
                        subject = loader.render_to_string(subject_template_name, c)
                        # Email subject *must not* contain newlines
                        subject = ''.join(subject.splitlines())
                        email = loader.render_to_string(email_template_name, c)
                        send_mail(subject, email, DEFAULT_FROM_EMAIL , [user.email], fail_silently=False)
                result = self.form_valid(form)
                messages.success(request, 'An email has been sent to ' + data +". Please check its inbox to continue reseting password.")
                return result
            result = self.form_invalid(form)
            messages.error(request, 'No user is associated with this email address')
            return result
        messages.error(request, 'Invalid Input')
        return self.form_invalid(form)

class PasswordResetConfirmView(FormView):
    template_name = "registration/reset_password_confirm.html"
    success_url = '/'
    form_class = SetPasswordForm

    def post(self, request, uidb64=None, token=None, *arg, **kwargs):
        """
        View that checks the hash in a password reset link and presents a
        form for entering a new password.
        """
        UserModel = get_user_model()
        form = self.form_class(request.POST)
        assert uidb64 is not None and token is not None  # checked by URLconf
        try:
            uid = urlsafe_base64_decode(uidb64)
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            if form.is_valid():
                new_password = form.cleaned_data['new_password2']
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password has been reset.')
                return self.form_valid(form)
            else:
                messages.error(
                    request, 'Password reset has not been unsuccessful.')
                return self.form_invalid(form)
        else:
            messages.error(
                request, 'The reset password link is no longer valid.')
            return self.form_invalid(form)

@method_decorator([login_required, student_required], name='dispatch')
class StudentInterestsView(UpdateView):
    model = Student
    form_class = StudentInterestsForm
    template_name = 'classroom/students/interests_form.html'
    success_url = reverse_lazy('students:quiz_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Interests updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    ordering = ('name', )
    context_object_name = 'courses'
    template_name = 'classroom/students/course_list.html'

    def get_queryset(self):
        student = self.request.user.student
        course_list = student.courses.values_list('pk', flat=True)
        queryset = Course.objects.filter(id__in=course_list)
        return queryset


@login_required
@student_required
def course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    student = request.user.student
    questions = Question.objects.filter(quiz__course=course)

    if request.method == 'POST':
        print(request.POST)
        question = get_object_or_404(Question, pk=request.POST.get('question_pk', None))
        if question.question_type == 'MC':
            submission = {
                'answer': request.POST.get('student_answer', None)
            }
        elif question.question_type == 'NU':
            answer = request.POST.get('student_answer', None)
            submission = {
                'answer': answer,
                'unit': request.POST.get('unit', None)
            }
            try:
                float(answer)
            except:
                messages.error(request, "Answer must be a valid float")
                return redirect('students:course', pk)
        StudentAnswer.objects.filter(student=student, question=question).delete()
        student_answer = StudentAnswer(student=student, question=question, submission=json.dumps(submission))
        student_answer.save()
        messages.success(request, 'Thank you for submitting your answer!')
        return redirect('students:course', pk)

    for q in questions:
        if q.is_active and len(StudentAnswer.objects.filter(question=q, student=student)) == 0:
            if q.question_type == 'MC':
                answer_data = parse_MC(q)
            elif q.question_type == 'NU':
                answer_data = parse_NU(q)
            return render(request, 'classroom/students/course.html', {
                'course': course,
                'active_question': True,
                'question': q,
                'answer_data': json.dumps(answer_data)
            })  

    return render(request, 'classroom/students/course.html', {
        'course': course, 
        'active_question': False,
        'firstname': student.user.first_name, 
        'lastname': student.user.last_name,
    })


@login_required
@student_required
def add_course(request):
    student = request.user.student

    if request.method == 'POST':
        form = CourseRegistrationForm(request.POST)
        if form.is_valid():
            course = Course.objects.filter(code=form.cleaned_data['code'])
            if len(course) == 0:
                messages.error(request, 'No course matches the inputted code. Try again')
                return redirect('students:course_add')
            else:
                student.courses.add(course[0])
                messages.success(request, 'Successfully registered course!')
                return redirect('students:course_list')
    else:
        form = CourseRegistrationForm()

    return render(request, 'classroom/students/course_add_form.html', {'student': student, 'form': form})


@method_decorator([login_required, student_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'classroom/students/quiz_list.html'

    def get_queryset(self):
        student = self.request.user.student
        student_interests = student.interests.values_list('pk', flat=True)
        taken_quizzes = student.quizzes.values_list('pk', flat=True)
        queryset = Quiz.objects.all() \
            .exclude(pk__in=taken_quizzes) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)
        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'classroom/students/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz') \
            .order_by('quiz__name')
        return queryset


@login_required
@student_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    student = request.user.student

    if student.quizzes.filter(pk=pk).exists():
        return render(request, 'students/taken_quiz.html')

    total_questions = quiz.questions.count()
    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('students:take_quiz', pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz, answer__is_correct=True).count()
                    score = round((correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz, score=score)
                    if score < 50.0:
                        messages.warning(request, 'Better luck next time! Your score for the quiz %s was %s.' % (quiz.name, score))
                    else:
                        messages.success(request, 'Congratulations! You completed the quiz %s with success! You scored %s points.' % (quiz.name, score))
                    return redirect('students:quiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'classroom/students/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })
