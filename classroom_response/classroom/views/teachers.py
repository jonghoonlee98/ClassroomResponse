from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.core import serializers

from ..decorators import teacher_required
from ..forms import BaseAnswerInlineFormSet, QuestionForm, QuestionAddForm, TeacherSignUpForm
from ..models import *

import json
import csv


class TeacherSignUpView(CreateView):
    model = User
    form_class = TeacherSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('teachers:course_change_list')


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseListView(ListView):
    model = Course
    ordering = ('name', )
    context_object_name = 'courses'
    template_name = 'classroom/teachers/course_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.courses.all()
        return queryset


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseCreateView(CreateView):
    model = Course
    fields = ('name', 'code')
    template_name = 'classroom/teachers/course_add_form.html'

    def form_valid(self, form):
        course = form.save(commit=False)
        course.owner = self.request.user
        course.save()
        messages.success(self.request, 'The course was created with success! Go ahead and add some quizzes now.')
        return redirect('teachers:course_change', course.pk)


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseUpdateView(UpdateView):
    model = Course
    fields = ('name', 'code')
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['quizzes'] = self.get_object().quizzes.annotate(questions_count=Count('questions'))
        kwargs['code'] = self.get_object().code
        print(self.get_object().code)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.courses.all()

    def get_success_url(self):
        return reverse('teachers:course_change', kwargs={'pk': self.object.pk})


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseDeleteView(DeleteView):
    model = Course
    context_object_name = 'course'
    template_name = 'classroom/teachers/course_delete_confirm.html'
    success_url = reverse_lazy('teachers:course_change_list')

    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, 'The course %s was deleted with success!' % course.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.courses.all()


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'classroom/teachers/quiz_change_list.html'

    def get_queryset(self):
        queryset = Quiz.objects.filter(course__id=self.kwargs['pk']) \
            .annotate(questions_count=Count('questions', distinct=True)) \
            .annotate(taken_count=Count('taken_quizzes', distinct=True))
        setattr(queryset, 'course_pk', self.kwargs['pk'])
        return queryset


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizCreateView(CreateView):
    model = Quiz
    fields = ('name', )
    template_name = 'classroom/teachers/quiz_add_form.html'

    def form_valid(self, form):
        quiz = form.save(commit=False)
        quiz.course = Course.objects.get(pk=self.kwargs['pk'])
        quiz.save()
        messages.success(self.request, 'The quiz was created with success! Go ahead and add some questions now.')
        return redirect('teachers:quiz_change', course_pk=self.kwargs['pk'], pk=quiz.pk)


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizUpdateView(UpdateView):
    model = Quiz
    fields = ('name', )
    context_object_name = 'quiz'
    template_name = 'classroom/teachers/quiz_change_form.html'

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        kwargs['course_pk'] = self.kwargs['course_pk']
        kwargs['course_name'] = Course.objects.get(pk=self.kwargs['course_pk']).name
        kwargs['quiz_pk'] = self.kwargs['pk']
        kwargs['questions'] = self.get_object().questions.annotate(answers_count=Count('answers'))
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing quizzes that belongs
        to the logged in user..user
        '''
        queryset = Quiz.objects.filter(course__owner=self.request.user)
        return queryset

    def get_success_url(self):
        return reverse('teachers:quiz_change', kwargs={'course_pk': self.kwargs['course_pk'],'pk': self.kwargs['pk']})


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizDeleteView(DeleteView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'classroom/teachers/quiz_delete_confirm.html'
    #success_url = reverse_lazy('teachers:quiz_change_list')

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        kwargs['course_pk'] = self.kwargs['course_pk']
        kwargs['quiz_pk'] = self.kwargs['pk']
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        quiz = self.get_object()
        messages.success(request, 'The quiz %s was deleted with success!' % quiz.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Quiz.objects.filter(course__owner=self.request.user)
        return queryset

    def get_success_url(self):
        return reverse('teachers:course_change', kwargs={'pk': self.kwargs['course_pk']})


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizResultsView(DetailView):
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'classroom/teachers/quiz_results.html'

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        taken_quizzes = quiz.taken_quizzes.select_related('student__user').order_by('-date')
        total_taken_quizzes = taken_quizzes.count()
        quiz_score = quiz.taken_quizzes.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_quizzes': taken_quizzes,
            'total_taken_quizzes': total_taken_quizzes,
            'quiz_score': quiz_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.quizzes.all()


@login_required
@teacher_required
def question_delete(request, course_pk, quiz_pk, question_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)
    Question.objects.filter(pk=question_pk).delete()
    return redirect('teachers:quiz_change', course_pk=course_pk, pk=quiz.pk)


@login_required
@teacher_required
def question_add(request, course_pk, pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    quiz = get_object_or_404(Quiz, pk=pk)

    if request.method == 'POST':
        form = QuestionAddForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.question_type = request.POST.get("Type", None)
            question.save()
            messages.success(request, 'You may now add answers/options to the question.')
            return redirect('teachers:question_change', course_pk, quiz.pk, question.pk)
    else:
        form = QuestionAddForm()

    return render(request, 'classroom/teachers/question_add_form.html', {'quiz': quiz, 'form': form, 'course_pk': course_pk})

@login_required
@teacher_required
def question_view(request, course_pk, quiz_pk, question_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)
    answers = Answer.objects.filter(question=question)

    if question.question_type == 'MC':
        if len(answers):
            data = json.loads(answers[0].data)
            answer = data['answer']

        return render(request, 'classroom/teachers/question_view.html', {
            'quiz': quiz,
            'question': question,
            'course_pk': course_pk,
            'course_name': Course.objects.get(pk=course_pk).name,
            'answers': answer,
        })

    elif question.question_type == 'NU':
        answer = ''
        units = None
        correct_unit = None

        if len(answers):
            data = json.loads(answers[0].data)
            answer = data['answer']
            if 'units' in data:
                units = data['units']
                correct_unit = data['correct_unit']

        return render(request, 'classroom/teachers/question_view.html', {
            'quiz': quiz,
            'question': question,
            'course_pk': course_pk,
            'course_name': Course.objects.get(pk=course_pk).name,
            'answer': answer,
            'correct_unit': correct_unit
        })



@login_required
@teacher_required
def question_change(request, course_pk, quiz_pk, question_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)
    if request.method == 'POST':
        if question.question_type == 'MC':
            form = QuestionForm(request.POST, request.FILES, instance=question)
            if form.is_valid():
                with transaction.atomic():
                    form.save()
                answers = []
                for x in range(0, 10):
                    text = request.POST.get('answer_' + str(x), None)
                    correct = request.POST.get('right_' + str(x), None)
                    right = False if correct is None else True 
                    if text is not None:
                        answer = {
                            'text': text,
                            'is_correct': right
                        }
                        answers.append(answer)
                Answer.objects.filter(question=question).delete()
                data = {
                    'answer' : answers
                }
                answer = Answer(data=json.dumps(data), question=question)
                answer.save()
                messages.success(request, 'Question and answers saved with success!')
                return redirect('teachers:question_view', course_pk, quiz.pk, question_pk)
        elif question.question_type == 'NU':
            form = QuestionForm(request.POST, request.FILES, instance=question)
            if form.is_valid():
                with transaction.atomic():
                    form.save()
                answer = request.POST.get('correct_answer', None)
                units = request.POST.getlist('units')
                Answer.objects.filter(question=question).delete()
                if len(units):           
                    data = {
                        'answer': answer,
                        'units': units,
                        'correct_unit': units[0]
                    }
                else:
                    data = {
                        'answer': answer
                    }

                try:
                    float(answer)
                except:
                    messages.error(request, "Answer must be a valid float")
                    return redirect('teachers:question_change', course_pk, quiz.pk, question_pk)

                answer = Answer(data=json.dumps(data), question=question)
                answer.save()
                messages.success(request, 'Question and answers saved with success!')
                return redirect('teachers:question_view', course_pk, quiz.pk, question_pk)

    else:
        form = QuestionForm(instance=question)

    if question.question_type == 'MC':
        answer = Answer.objects.filter(question=question)

        answers = None

        if len(answer):
            data = json.loads(answer[0].data)
            answers = data['answer']

        return render(request, 'classroom/teachers/question_change_form.html', {
            'quiz': quiz,
            'question': question,
            'form': form,
            'course_pk': course_pk,
            'course_name': Course.objects.get(pk=course_pk).name,
            'answers': answers
        })

    elif question.question_type == 'NU':
        answers = Answer.objects.filter(question=question)

        answer = ''
        units = None
        correct_unit = None

        if len(answers):
            data = json.loads(answers[0].data)
            answer = data['answer']
            if 'units' in data:
                units = data['units']
                correct_unit = data['correct_unit']
                print(correct_unit)

        return render(request, 'classroom/teachers/question_change_form.html', {
            'quiz': quiz,
            'question': question,
            'form': form,
            'course_pk': course_pk,
            'course_name': Course.objects.get(pk=course_pk).name,
            'answer': answer,
            'units': units,
            'correct_unit': correct_unit
        })

@login_required
@teacher_required
def question_activate(request, course_pk, quiz_pk, question_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)
    all_questions = Question.objects.filter(quiz__course__owner=request.user)

    all_questions.update(is_active=False)

    question.is_active = True
    question.save()

    return render(request, 'classroom/teachers/question_active.html', {
        'quiz': quiz,
        'question': question,
    })


@login_required
@teacher_required
def question_deactivate(request, course_pk, quiz_pk, question_pk):
    question = get_object_or_404(Question, pk=question_pk)
    question.is_active = False
    question.save()

    return redirect('teachers:question_result', course_pk, quiz_pk, question_pk)


@login_required
@teacher_required
def question_result(request, course_pk, quiz_pk, question_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)
    student_answers = StudentAnswer.objects.filter(question=question).values_list('submission')
    answer = Answer.objects.filter(question=question)
    answers = None
    unit = None
    submissions = []
    print(list(student_answers))

    if question.question_type == 'MC':
        for a in list(student_answers):
            submissions.append(json.loads(a[0]))
    elif question.question_type == 'NU':
        for a in list(student_answers):
            submissions.append(json.loads(a[0]))

    if len(answer):
        data = json.loads(answer[0].data)
        answers = data['answer']
        if question.question_type == 'NU':
            try:
                unit = data['correct_unit']
            except:
                unit = None


    return render(request, 'classroom/teachers/question_result.html', {
        'quiz': quiz,
        'question': question,
        'course_pk': course_pk,
        'course_name': Course.objects.get(pk=course_pk).name,
        'student_answers': json.dumps(submissions),
        'answers': json.dumps(answers),
        'unit': unit
    })


@login_required
@teacher_required
def question_result_csv(request, course_pk, quiz_pk, question_pk):
    question = get_object_or_404(Question, pk=question_pk)
    student_answers = StudentAnswer.objects.filter(question=question).values_list('submission')
    print(student_answers)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="' + question.text + '.csv"'

    writer = csv.writer(response)
    writer.writerow([question.text + '\n'])
    for a in list(student_answers):
        data = json.loads(a[0])
        if 'unit' in data:
            writer.writerow([data['answer'], data['unit']])
        else:
            writer.writerow([data['answer']])

    return response


@method_decorator([login_required, teacher_required], name='dispatch')
class QuestionDeleteView(DeleteView):
    model = Question
    context_object_name = 'question'
    template_name = 'classroom/teachers/question_delete_confirm.html'
    pk_url_kwarg = 'question_pk'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        kwargs['quiz'] = question.quiz
        kwargs['course_pk'] = self.kwargs['course_pk']
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        messages.success(request, 'The question %s was deleted with success!' % question.text)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Question.objects.filter(quiz__course__owner=self.request.user)

    def get_success_url(self):
        question = self.get_object()
        return reverse('teachers:quiz_change', kwargs={'pk': question.quiz_id, 'course_pk': self.kwargs['course_pk']})









