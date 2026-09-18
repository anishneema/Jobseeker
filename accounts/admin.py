from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import RecruiterProfile, JobSeekerProfile

class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('role',)

    def role(self, user):
        if hasattr(user, 'recruiter_profile'):
            return 'Recruiter'
        if hasattr(user, 'jobseeker_profile'):
            return 'Job Seeker'
        return '-'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(RecruiterProfile)
admin.site.register(JobSeekerProfile)