from django.db import models
from django.contrib.auth.models import User


class JobPosting(models.Model):
    REMOTE_ONSITE_CHOICES = [
        ('remote', 'Remote'),
        ('on-site', 'On-site'),
        ('hybrid', 'Hybrid'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_postings'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    skills_required = models.CharField(
        max_length=500,
        help_text='Comma-separated skills, e.g. Python, Django, SQL'
    )
    location = models.CharField(max_length=200)
    salary_min = models.PositiveIntegerField()
    salary_max = models.PositiveIntegerField()
    remote_onsite = models.CharField(
        max_length=20,
        choices=REMOTE_ONSITE_CHOICES
    )
    visa_sponsorship = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    date_posted = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return f'{self.id} - {self.title}'

    def salary_range(self):
        return f'${self.salary_min:,} - ${self.salary_max:,}'

    def company_name(self):
        profile = getattr(self.recruiter, 'recruiter_profile', None)
        if profile:
            return profile.company_name
        return self.recruiter.username
