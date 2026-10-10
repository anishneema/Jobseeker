from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .forms import MessageForm
from .models import Message


@login_required
def inbox(request):
    template_data = {}
    if hasattr(request.user, 'recruiter_profile'):
        template_data['title'] = 'Sent Messages'
        template_data['mode'] = 'sent'
        template_data['message_list'] = Message.objects.filter(
            sender=request.user
        ).select_related('recipient')
    elif hasattr(request.user, 'jobseeker_profile'):
        template_data['title'] = 'Inbox'
        template_data['mode'] = 'received'
        template_data['message_list'] = Message.objects.filter(
            recipient=request.user
        ).select_related('sender', 'sender__recruiter_profile')
    else:
        return redirect('home.index')
    return render(request, 'messaging/inbox.html',
                  {'template_data': template_data})


@login_required
def compose(request, user_id):
    if not hasattr(request.user, 'recruiter_profile'):
        messages.error(request, 'Only recruiters can send messages.')
        return redirect('home.index')
    recipient = get_object_or_404(
        User, id=user_id, jobseeker_profile__isnull=False
    )
    template_data = {}
    template_data['title'] = 'New Message'
    template_data['recipient'] = recipient
    if request.method == 'GET':
        template_data['form'] = MessageForm()
        return render(request, 'messaging/compose.html',
                      {'template_data': template_data})
    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.sender = request.user
        message.recipient = recipient
        message.save()
        messages.success(request, f'Message sent to {recipient.username}.')
        return redirect('messaging.inbox')
    template_data['form'] = form
    return render(request, 'messaging/compose.html',
                  {'template_data': template_data})


@login_required
def detail(request, id):
    message = get_object_or_404(
        Message.objects.select_related(
            'sender', 'sender__recruiter_profile', 'recipient'
        ),
        Q(sender=request.user) | Q(recipient=request.user),
        id=id,
    )
    if message.recipient_id == request.user.id:
        message.mark_read()
    template_data = {}
    template_data['title'] = 'Message'
    template_data['message'] = message
    template_data['is_recipient'] = message.recipient_id == request.user.id
    return render(request, 'messaging/detail.html',
                  {'template_data': template_data})
