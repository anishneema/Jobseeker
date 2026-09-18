from django.db import models
from django.contrib.auth.models import User


class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='recruiter_profile'
    )
    company_name = models.CharField(max_length=255)

    def __str__(self):
        return self.company_name

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='jobseeker_profile')
    headline = models.CharField(max_length=255, blank=True)
    skills = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated skills, e.g. Python, Django, SQL'
    )
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    links = models.TextField(
        blank=True,
        help_text='One link per line, e.g. LinkedIn, GitHub, portfolio'
    )
    show_skills = models.BooleanField(default=True)
    show_education = models.BooleanField(default=True)
    show_work_experience = models.BooleanField(default=True)
    show_links = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username