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
from ..forms import StudentInterestsForm, StudentSignUpForm, TakeQuizForm, CourseRegistrationForm
from ..models import *
from ..parse_data import *

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
        print('jong')
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
        confidence = request.POST.get('confidence', None)
        if confidence is not None:
            submission['confidence'] = confidence
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
