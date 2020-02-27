from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(User)
admin.site.register(Course)
admin.site.register(Quiz)
admin.site.register(Student)
admin.site.register(Question)
admin.site.register(Subject)