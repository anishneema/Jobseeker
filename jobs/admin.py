from django.contrib import admin
from .models import JobPosting

class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'recruiter', 'location', 'status', 'date_posted')
    list_filter = ('status', 'remote_onsite', 'visa_sponsorship')
    search_fields = ('title', 'description', 'skills_required', 'location')
    actions = ['close_postings']

    @admin.action(description='Close selected job postings')
    def close_postings(self, request, queryset):
        count = queryset.update(status='closed')
        self.message_user(request, f'{count} posting(s) closed.')

admin.site.register(JobPosting, JobPostingAdmin)
