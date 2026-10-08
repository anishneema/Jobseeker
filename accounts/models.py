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
    location = models.CharField(max_length=200, blank=True)
    projects = models.TextField(blank =True)
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
    
    commute_radius_miles = models.PositiveSmallIntegerField(null=True, blank=True)
    home_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    home_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    def __str__(self):
        return self.user.username
    
class SavedCandidateSearch(models.Model):
    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_candidate_searches'
    )
    skills = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=200, blank=True)
    projects = models.CharField(max_length=500, blank=True)
    seen_candidate_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Saved search by {self.recruiter.username}'
