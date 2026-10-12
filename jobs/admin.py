from django.contrib import admin
from django.utils import timezone
from .models import JobPosting, Application, CartItem, ContentReport
from .admin_exports import csv_export


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'recruiter', 'location', 'status', 'is_removed', 'date_posted')
    list_filter = ('is_removed', 'status', 'remote_onsite', 'visa_sponsorship')
    search_fields = ('title', 'description', 'skills_required', 'location')
    actions = ['close_postings', 'remove_postings', 'restore_postings', 'export_csv']
    export_csv = csv_export('jobs', ('id', 'title', 'recruiter__username', 'location',
                                   'salary_min', 'salary_max', 'remote_onsite',
                                   'status', 'is_removed', 'date_posted'))

    @admin.action(description='Close selected job postings', permissions=['change'])
    def close_postings(self, request, queryset):
        count = queryset.update(status='closed')
        self.log_changes(request, queryset, 'Closed posting')
        self.message_user(request, f'{count} posting(s) closed.')

    @admin.action(description='Remove selected postings from the platform', permissions=['change'])
    def remove_postings(self, request, queryset):
        count = queryset.update(is_removed=True)
        self.log_changes(request, queryset, 'Removed posting from platform')
        self.message_user(request, f'{count} posting(s) removed. Applications and reports are preserved.')

    @admin.action(description='Restore selected removed postings', permissions=['change'])
    def restore_postings(self, request, queryset):
        count = queryset.update(is_removed=False)
        self.log_changes(request, queryset, 'Restored posting')
        self.message_user(request, f'{count} posting(s) restored.')

    def log_changes(self, request, queryset, message):
        for job in queryset:
            self.log_change(request, job, message)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'status', 'date_applied')
    list_filter = ('status', 'date_applied')
    actions = ['export_csv']
    export_csv = csv_export('applications', ('id', 'job_id', 'job__title',
                                            'applicant__username', 'status', 'date_applied'))


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ('target_label', 'reason', 'reporter', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('target_label', 'details', 'review_notes', 'reporter__username')
    readonly_fields = ('reporter', 'job', 'reported_user', 'target_label', 'content_snapshot',
                       'reason', 'details', 'created_at', 'reviewed_by', 'reviewed_at')
    fields = readonly_fields + ('status', 'review_notes')
    actions = ['export_csv']
    export_csv = csv_export('reports', ('id', 'target_label', 'reporter__username',
                                      'reason', 'status', 'created_at',
                                      'reviewed_by__username', 'reviewed_at'))

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data or 'review_notes' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


admin.site.register(CartItem)
