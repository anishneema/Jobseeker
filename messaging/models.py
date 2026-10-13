from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender.username} -> {self.recipient.username}'

    def is_read(self):
        return self.read_at is not None

    def mark_read(self):
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

    def sender_label(self):
        profile = getattr(self.sender, 'recruiter_profile', None)
        if profile:
            return f'{self.sender.username} ({profile.company_name})'
        return self.sender.username
