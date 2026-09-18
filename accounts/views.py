from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignUpForm, CustomErrorList, JobSeekerProfileForm
from .models import RecruiterProfile, JobSeekerProfile
from django.contrib import messages


def jobseeker_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'jobseeker_profile'):
            messages.error(request, 'Only job seekers can edit a profile.')
            return redirect('home.index')
        return view_func(request, *args, **kwargs)
    return wrapper

def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html',
                      {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html',
                          {'template_data': template_data})
        auth_login(request, user)
        return redirect('home.index')


def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = SignUpForm()
        return render(request, 'accounts/register.html',
                      {'template_data': template_data})
    elif request.method == 'POST':
        form = SignUpForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            user = form.save()
            if form.cleaned_data['role'] == 'recruiter':
                RecruiterProfile.objects.create(
                    user=user,
                    company_name=form.cleaned_data['company_name'].strip()
                )
            else:
                JobSeekerProfile.objects.create(user=user)
            return redirect('accounts.login')
        template_data['form'] = form
        return render(request, 'accounts/register.html',
                      {'template_data': template_data})


@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')

@jobseeker_required
def profile_edit(request):
    profile = request.user.jobseeker_profile
    template_data = {}
    template_data['title'] = 'My Profile'
    if request.method == 'GET':
        template_data['form'] = JobSeekerProfileForm(instance=profile)
        return render(request, 'accounts/profile_edit.html',
                      {'template_data': template_data})
    form = JobSeekerProfileForm(request.POST, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('accounts.profile_edit')
    template_data['form'] = form
    return render(request, 'accounts/profile_edit.html',
                  {'template_data': template_data})


@login_required
def profile_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(JobSeekerProfile, user=user)
    is_owner = request.user.id == user.id
    template_data = {}
    template_data['title'] = f'{user.username} - Profile'
    template_data['profile'] = profile
    template_data['is_owner'] = is_owner
    template_data['show_skills'] = is_owner or (profile.show_skills and bool(profile.skills))
    template_data['show_education'] = is_owner or (profile.show_education and bool(profile.education))
    template_data['show_work_experience'] = is_owner or (
        profile.show_work_experience and bool(profile.work_experience)
    )
    template_data['show_links'] = is_owner or (profile.show_links and bool(profile.links))
    return render(request, 'accounts/profile_view.html',
                  {'template_data': template_data})