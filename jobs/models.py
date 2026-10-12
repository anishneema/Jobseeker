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
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
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
    is_removed = models.BooleanField(default=False, help_text='Hidden by an administrator; recruiters cannot restore this posting.')

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


class Application(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('review', 'Review'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('closed', 'Closed'),
    ]

    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    note = models.TextField(
        blank=True,
        help_text='A short note tailored to this job (optional).'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='applied'
    )
    date_applied = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_applied']
        unique_together = ('job', 'applicant')

    def __str__(self):
        return f'{self.applicant.username} -> {self.job.title}'

    def status_badge_class(self):
        return {
            'applied': 'text-bg-secondary',
            'review': 'text-bg-info',
            'interview': 'text-bg-primary',
            'offer': 'text-bg-success',
            'closed': 'text-bg-dark',
        }[self.status]

class CartItem(models.Model):
    jobseeker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']
        unique_together = ('jobseeker', 'job')

    def __str__(self):
        return f'{self.jobseeker.username} -> {self.job.title} (cart)'


class ContentReport(models.Model):
    REASON_CHOICES = [('spam', 'Spam'), ('misleading', 'Misleading content'),
                      ('abuse', 'Abuse or harassment'), ('other', 'Other')]
    STATUS_CHOICES = [('pending', 'Pending'), ('investigating', 'Investigating'),
                      ('resolved', 'Resolved'), ('dismissed', 'Dismissed')]
    reporter = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='submitted_reports')
    job = models.ForeignKey(JobPosting, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    reported_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_reports')
    target_label = models.CharField(max_length=255)
    content_snapshot = models.TextField(blank=True)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_reports')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.target_label}: {self.get_reason_display()}'
