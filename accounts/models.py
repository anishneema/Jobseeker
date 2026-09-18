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
