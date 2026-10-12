import csv
import io
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse
from accounts.models import JobSeekerProfile, RecruiterProfile
from .models import JobPosting, Application, ContentReport


class ModerationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin', password='pw')
        self.recruiter = User.objects.create_user('recruiter', password='pw')
        RecruiterProfile.objects.create(user=self.recruiter, company_name='Acme')
        self.seeker = User.objects.create_user('seeker', password='pw')
        JobSeekerProfile.objects.create(user=self.seeker, skills='Python')
        self.job = JobPosting.objects.create(recruiter=self.recruiter,
            title='Engineer', description='Build things', skills_required='Python',
            location='Remote', salary_min=10, salary_max=20, remote_onsite='remote')

    def action(self, model, action, ids):
        return self.client.post(reverse(f'admin:{model}_changelist'), {
            'action': action, '_selected_action': ids})

    def test_removal_hides_job_and_preserves_application(self):
        application = Application.objects.create(job=self.job, applicant=self.seeker)
        self.client.force_login(self.admin)
        self.action('jobs_jobposting', 'remove_postings', [self.job.pk])
        self.job.refresh_from_db()
        self.assertTrue(self.job.is_removed)
        self.assertTrue(LogEntry.objects.filter(object_id=str(self.job.pk)).exists())
        self.client.force_login(self.seeker)
        self.assertNotContains(self.client.get(reverse('jobs.index')), 'Engineer')
        self.assertNotContains(self.client.get(reverse('jobs.recommendations')), 'Engineer')
        self.assertEqual(self.client.get(reverse('jobs.show', args=[self.job.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('jobs.apply', args=[self.job.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('jobs.cart_add', args=[self.job.pk])).status_code, 404)
        self.assertTrue(Application.objects.filter(pk=application.pk).exists())
        self.client.force_login(self.admin)
        self.action('jobs_jobposting', 'restore_postings', [self.job.pk])
        self.assertEqual(self.client.get(reverse('jobs.show', args=[self.job.pk])).status_code, 200)

    def test_recruiter_cannot_restore_through_edit_form(self):
        self.job.is_removed = True
        self.job.save()
        self.client.force_login(self.recruiter)
        self.client.post(reverse('jobs.edit', args=[self.job.pk]), {
            'title': 'Updated', 'description': 'New', 'skills_required': 'Python',
            'location': 'Remote', 'salary_min': 10, 'salary_max': 20,
            'remote_onsite': 'remote', 'status': 'open', 'is_removed': ''})
        self.job.refresh_from_db()
        self.assertTrue(self.job.is_removed)

    def test_reports_validate_and_keep_snapshot_after_deletion(self):
        url = reverse('jobs.report_content', args=['job', self.job.pk])
        self.assertEqual(self.client.post(url, {'reason': 'spam', 'details': 'Spam'}).status_code, 302)
        self.assertFalse(ContentReport.objects.exists())
        self.client.force_login(self.seeker)
        self.client.get(url)
        self.client.post(url, {'reason': 'spam', 'details': '   '})
        self.assertFalse(ContentReport.objects.exists())
        self.client.post(url, {'reason': 'spam', 'details': 'Misleading role', 'status': 'resolved'})
        report = ContentReport.objects.get()
        self.assertEqual(report.reporter, self.seeker)
        self.assertEqual(report.status, 'pending')
        self.job.delete()
        report.refresh_from_db()
        self.assertIsNone(report.job)
        self.assertIn('Build things', report.content_snapshot)
        self.assertIn('Engineer', report.target_label)
        self.client.post(reverse('jobs.report_content', args=['user', self.recruiter.pk]),
                         {'reason': 'abuse', 'details': 'Harassment'})
        self.assertTrue(ContentReport.objects.filter(reported_user=self.recruiter).exists())

    def test_admin_review_tracks_reviewer_without_automatic_removal(self):
        report = ContentReport.objects.create(reporter=self.seeker, job=self.job,
            target_label='Engineer', reason='spam', details='Spam')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin:jobs_contentreport_change', args=[report.pk]),
            {'status': 'investigating', 'review_notes': 'Checking employer', '_save': 'Save'})
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.reviewed_by, self.admin)
        self.assertIsNotNone(report.reviewed_at)
        self.assertEqual(report.review_notes, 'Checking employer')
        self.job.refresh_from_db()
        self.assertFalse(self.job.is_removed)

    def test_exports_are_selected_safe_and_permission_protected(self):
        self.job.title = '=HYPERLINK("bad"),test'
        self.job.save()
        self.client.force_login(self.seeker)
        response = self.action('jobs_jobposting', 'export_csv', [self.job.pk])
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.admin)
        response = self.action('jobs_jobposting', 'export_csv', [self.job.pk])
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][1], "'" + self.job.title)
        response = self.action('auth_user', 'export_csv', [self.seeker.pk])
        rows = list(csv.reader(io.StringIO(response.content.decode())))
        self.assertEqual(len(rows), 2)
        self.assertNotIn('password', rows[0])
        self.assertEqual(rows[1][1], 'seeker')
        for model, obj in [('jobs_application', Application.objects.create(job=self.job, applicant=self.seeker)),
                           ('jobs_contentreport', ContentReport.objects.create(reporter=self.seeker,
                            job=self.job, target_label='Engineer', reason='spam', details='Spam'))]:
            response = self.action(model, 'export_csv', [obj.pk])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(list(csv.reader(io.StringIO(response.content.decode())))), 2)

    def test_staff_without_model_permission_cannot_review_or_export(self):
        staff = User.objects.create_user('staff', password='pw', is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('admin:jobs_contentreport_changelist')).status_code, 403)
        self.assertEqual(self.action('jobs_jobposting', 'export_csv', [self.job.pk]).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(codename='view_jobposting'))
        self.assertEqual(self.action('jobs_jobposting', 'export_csv', [self.job.pk]).status_code, 200)
        self.action('jobs_jobposting', 'remove_postings', [self.job.pk])
        self.job.refresh_from_db()
        self.assertFalse(self.job.is_removed)
