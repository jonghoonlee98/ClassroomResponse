from django.urls import include, path

from .views import classroom, students, teachers

urlpatterns = [
    path('', classroom.home, name='home'),

    path('students/', include(([
        path('', students.CourseListView.as_view(), name='course_list'),
        path('course/<int:pk>/', students.course, name='course'),
        #path('course/add/', students.CourseRegisterView.as_view(), name='course_add'),
        path('course/add/', students.add_course, name='course_add'),
        path('quiz/', students.QuizListView.as_view(), name='quiz_list'),
        path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
        path('taken/', students.TakenQuizListView.as_view(), name='taken_quiz_list'),
        path('quiz/<int:pk>/', students.take_quiz, name='take_quiz'),
    ], 'classroom'), namespace='students')),

    path('teachers/', include(([
        path('', teachers.CourseListView.as_view(), name='course_change_list'),
        path('course/add/', teachers.CourseCreateView.as_view(), name='course_add'),
        path('course/<int:pk>/', teachers.CourseUpdateView.as_view(), name='course_change'),
        path('course/<int:pk>/delete/', teachers.CourseDeleteView.as_view(), name='course_delete'),

        path('course/<int:pk>/quiz/', teachers.QuizListView.as_view(), name='quiz_change_list'),
        path('course/<int:pk>/quiz/add/', teachers.QuizCreateView.as_view(), name='quiz_add'),
        path('course/<int:course_pk>/quiz/<int:pk>/', teachers.QuizUpdateView.as_view(), name='quiz_change'),
        path('course/<int:course_pk>/quiz/<int:pk>/delete/', teachers.QuizDeleteView.as_view(), name='quiz_delete'),
        path('course/<int:course_pk>/quiz/<int:pk>/results/', teachers.QuizResultsView.as_view(), name='quiz_results'),
        path('course/<int:course_pk>/quiz/<int:pk>/question/add/', teachers.question_add, name='question_add'),
        path('course/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/', teachers.question_view, name='question_view'),
        path('course/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/delete/', teachers.question_delete, name='question_delete'),
        path('course/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/change/', teachers.question_change, name='question_change'),
        path('course/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/activate/', teachers.question_activate, name='question_activate'),
        path('course/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/deactivate/', teachers.question_deactivate, name='question_deactivate'),
        path('course/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/result/', teachers.question_result, name='question_result'),
        path('course/<int:course_pk>/quiz/<int:quiz_pk>/question/<int:question_pk>/csv/', teachers.question_result_csv, name='question_result_csv')
    ], 'classroom'), namespace='teachers')),
]
