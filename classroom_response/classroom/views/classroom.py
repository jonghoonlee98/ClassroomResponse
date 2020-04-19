from django.shortcuts import redirect, render
import os

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
from ..forms import PasswordResetRequestForm, SetPasswordForm


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'

class ResetPasswordRequestView(FormView):
    template_name = "registration/forgot_template.html"
    success_url = '../login'
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
                        print(default_token_generator.make_token(user))
                        c = {
                            'email': user.email,
                            'domain': request.META['HTTP_HOST'],
                            'site_name': 'classroomresponsesystem.herokuapp.com',
                            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                            'user': user,
                            'token': default_token_generator.make_token(user),
                            'protocol': 'http' if os.environ.get('HOSTNAME') == None else 'https',
                            }
                        subject_template_name='registration/password_reset_subject.txt'
                        email_template_name='registration/password_reset_email.html'
                        subject = loader.render_to_string(subject_template_name, c)
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
        UserModel = User
        form = self.form_class(request.POST)
        assert uidb64 is not None and token is not None 
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            print('user is none')
            
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


def home(request):
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:course_change_list')
        else:
            return redirect('students:course_list')
    return render(request, 'classroom/home.html')
