from django.urls import include, path
from django.contrib import admin

from classroom.views import classroom, students, teachers

from . import settings
from django.contrib.staticfiles.urls import static
from django.conf.urls.static import static as static_url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import url

urlpatterns = [
    path('', include('classroom.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', classroom.SignUpView.as_view(), name='signup'),
    path('accounts/signup/student/', students.StudentSignUpView.as_view(), name='student_signup'),
    path('accounts/signup/teacher/', teachers.TeacherSignUpView.as_view(), name='teacher_signup'),
    path('accounts/reset_password_confirm/<uidb64>/<token>/', classroom.PasswordResetConfirmView.as_view(), name='reset_password_confirm'),
    path('accounts/resetpassword/', classroom.ResetPasswordRequestView.as_view(), name="reset_password"),
    path('admin/', admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static_url(settings.STATIC_URL, document_root=settings.STATIC_ROOT)