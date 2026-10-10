from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import JobSeekerProfile, RecruiterProfile
from .models import Message


class MessagingTests(TestCase):
    def test_recruiter_message_reaches_candidate_and_stays_private(self):
        recruiter = User.objects.create_user(username='msgboss', password='pw')
        RecruiterProfile.objects.create(user=recruiter, company_name='Acme')
        seeker = User.objects.create_user(username='msgseeker', password='pw')
        JobSeekerProfile.objects.create(user=seeker)
        stranger = User.objects.create_user(username='msgstranger', password='pw')
        JobSeekerProfile.objects.create(user=stranger)

        self.client.login(username='msgboss', password='pw')
        compose = reverse('messaging.compose', kwargs={'user_id': seeker.id})
        response = self.client.post(compose, {'body': 'Are you free Friday?'})
        self.assertRedirects(response, reverse('messaging.inbox'))
        message = Message.objects.get()
        self.client.logout()

        self.client.login(username='msgseeker', password='pw')
        inbox = self.client.get(reverse('messaging.inbox'))
        self.assertContains(inbox, 'msgboss (Acme)')
        self.assertEqual(inbox.context['unread_message_count'], 1)
        detail = reverse('messaging.detail', kwargs={'id': message.id})
        self.client.get(detail)
        message.refresh_from_db()
        self.assertTrue(message.is_read())
        self.client.logout()

        self.client.login(username='msgstranger', password='pw')
        self.assertEqual(self.client.get(detail).status_code, 404)
