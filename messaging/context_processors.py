from .models import Message


def unread_count(request):
    count = 0
    if request.user.is_authenticated:
        count = Message.objects.filter(
            recipient=request.user, read_at__isnull=True
        ).count()
    return {'unread_message_count': count}
