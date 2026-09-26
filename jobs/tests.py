from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import JobSeekerProfile, RecruiterProfile
from .models import Application, JobPosting


class ApplicationTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter', password='pw')
        RecruiterProfile.objects.create(user=self.recruiter, company_name='Acme')
        self.seeker = User.objects.create_user(username='seeker', password='pw')
        JobSeekerProfile.objects.create(user=self.seeker)
        self.job = JobPosting.objects.create(
            recruiter=self.recruiter,
            title='Backend Engineer',
            description='Build things.',
            skills_required='Python, Django',
            location='Remote',
            salary_min=100000,
            salary_max=150000,
            remote_onsite='remote',
        )

    def test_jobseeker_can_apply_with_note(self):
        self.client.login(username='seeker', password='pw')
        response = self.client.post(
            reverse('jobs.apply', kwargs={'id': self.job.id}),
            {'note': 'I would love to work on this.'},
        )
        self.assertRedirects(response, reverse('jobs.show', kwargs={'id': self.job.id}))
        application = Application.objects.get(job=self.job, applicant=self.seeker)
        self.assertEqual(application.note, 'I would love to work on this.')
        self.assertEqual(application.status, 'applied')

    def test_jobseeker_cannot_apply_twice(self):
        Application.objects.create(job=self.job, applicant=self.seeker)
        self.client.login(username='seeker', password='pw')
        self.client.post(reverse('jobs.apply', kwargs={'id': self.job.id}), {'note': 'again'})
        self.assertEqual(
            Application.objects.filter(job=self.job, applicant=self.seeker).count(), 1
        )

    def test_recruiter_cannot_apply(self):
        self.client.login(username='recruiter', password='pw')
        response = self.client.post(
            reverse('jobs.apply', kwargs={'id': self.job.id}), {'note': ''}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Application.objects.filter(job=self.job).exists())

    def test_cannot_apply_to_closed_job(self):
        self.job.status = 'closed'
        self.job.save()
        self.client.login(username='seeker', password='pw')
        self.client.post(reverse('jobs.apply', kwargs={'id': self.job.id}), {'note': ''})
        self.assertFalse(Application.objects.filter(job=self.job).exists())


class ApplicationStatusTrackingTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(username='recruiter2', password='pw')
        RecruiterProfile.objects.create(user=self.recruiter, company_name='Acme')
        self.seeker = User.objects.create_user(username='seeker2', password='pw')
        JobSeekerProfile.objects.create(user=self.seeker)
        self.other_seeker = User.objects.create_user(username='seeker3', password='pw')
        JobSeekerProfile.objects.create(user=self.other_seeker)
        self.job = JobPosting.objects.create(
            recruiter=self.recruiter,
            title='Backend Engineer',
            description='Build things.',
            skills_required='Python, Django',
            location='Remote',
            salary_min=100000,
            salary_max=150000,
            remote_onsite='remote',
        )

    def test_my_applications_only_shows_own_applications(self):
        Application.objects.create(job=self.job, applicant=self.seeker, status='interview')
        Application.objects.create(job=self.job, applicant=self.other_seeker, status='offer')
        self.client.login(username='seeker2', password='pw')
        response = self.client.get(reverse('jobs.my_applications'))
        self.assertContains(response, 'Interview')
        self.assertNotContains(response, 'Offer')

    def test_recruiter_cannot_view_my_applications(self):
        self.client.login(username='recruiter2', password='pw')
        response = self.client.get(reverse('jobs.my_applications'))
        self.assertEqual(response.status_code, 302)

    def test_status_badge_class_for_each_status(self):
        application = Application.objects.create(job=self.job, applicant=self.seeker)
        for status, _ in Application.STATUS_CHOICES:
            application.status = status
            self.assertTrue(application.status_badge_class())
