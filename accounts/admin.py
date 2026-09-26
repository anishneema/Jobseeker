from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import RecruiterProfile, JobSeekerProfile

class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('role', 'is_active')
    actions = ['make_job_seeker', 'make_recruiter',
               'deactivate_users', 'activate_users']

    def role(self, user):
        if hasattr(user, 'recruiter_profile'):
            return 'Recruiter'
        if hasattr(user, 'jobseeker_profile'):
            return 'Job Seeker'
        return '-'

    @admin.action(description='Change role to Job Seeker')
    def make_job_seeker(self, request, queryset):
        for user in queryset:
            RecruiterProfile.objects.filter(user=user).delete()
            JobSeekerProfile.objects.get_or_create(user=user)
        self.message_user(
            request, f'{queryset.count()} user(s) are now job seekers.'
        )

    @admin.action(description='Change role to Recruiter')
    def make_recruiter(self, request, queryset):
        for user in queryset:
            JobSeekerProfile.objects.filter(user=user).delete()
            RecruiterProfile.objects.get_or_create(
                user=user, defaults={'company_name': user.username}
            )
        self.message_user(
            request, f'{queryset.count()} user(s) are now recruiters.'
        )

    @admin.action(description='Deactivate selected users (blocks login)')
    def deactivate_users(self, request, queryset):
        count = queryset.exclude(id=request.user.id).update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated.')

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} user(s) activated.')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(RecruiterProfile)
admin.site.register(JobSeekerProfile)
