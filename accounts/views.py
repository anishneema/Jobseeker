from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from .forms import SignUpForm, CustomErrorList, JobSeekerProfileForm, EmailCandidateForm
from .models import RecruiterProfile, JobSeekerProfile, SavedCandidateSearch
from django.contrib import messages
from django.views.decorators.http import require_POST

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
    template_data['show_work_experience'] = (profile.show_work_experience and bool(profile.work_experience))
    template_data['show_links'] = is_owner or (profile.show_links and bool(profile.links))
    return render(request, 'accounts/profile_view.html',
                  {'template_data': template_data})

def get_matching_candidates(skills='', location='', projects=''):
    candidates = JobSeekerProfile.objects.all()
    if skills:
        candidates = candidates.filter(skills__icontains=skills)
    if location:
        candidates = candidates.filter(location__icontains=location)
    if projects:
        candidates = candidates.filter(projects__icontains=projects)
    return candidates

@login_required
def candidate_search(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('home.index')
    candidates = get_matching_candidates(skills, location, projects)
    skills = request.GET.get('skills', '').strip()
    location = request.GET.get('location', '').strip()
    projects = request.GET.get('projects', '').strip()
    if skills:
        candidates = candidates.filter(skills__icontains=skills)
    if location:
        candidates = candidates.filter(location__icontains=location)
    if projects:
        candidates = candidates.filter(projects__icontains=projects)
    template_data = {
        'title' : 'Search Candidates',
        'candidates' : candidates,
        'skills' : skills,
        'location' : location,
        'projects' : projects,
    }
    return render(
        request, 'accounts/candidate_search.html',
        {'template_data': template_data}
    )


@login_required
def email_candidate(request, user_id):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('home.index')
    profile = get_object_or_404(JobSeekerProfile, user__id=user_id)
    candidate = profile.user
    if not candidate.email:
        messages.error(request, 'This candidate has no email on file.')
        return redirect('accounts.candidate_search')
    template_data = {}
    template_data['title'] = 'Send Email'
    template_data['candidate'] = candidate
    if request.method == 'GET':
        template_data['form'] = EmailCandidateForm()
        return render(request, 'accounts/email_candidate.html',
                      {'template_data': template_data})
    form = EmailCandidateForm(request.POST)
    if form.is_valid():
        email = EmailMessage(
            subject=form.cleaned_data['subject'],
            body=form.cleaned_data['body'],
            to=[candidate.email],
            reply_to=[request.user.email],
        )
        email.send()
        messages.success(request, f'Email sent to {candidate.username}.')
        return redirect('accounts.candidate_search')
    template_data['form'] = form
    return render(request, 'accounts/email_candidate.html',
                  {'template_data': template_data})

@require_POST
@login_required
def save_candidate_search(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('home.index')

    skills = request.POST.get('skills', '').strip()
    location = request.POST.get('location', '').strip()
    projects = request.POST.get('projects', '').strip()

    if not (skills or location or projects):
        messages.error(request, 'Enter at least one search filter.')
        return redirect('accounts.candidate_search')

    matching_ids = list(
        get_matching_candidates(
            skills, location, projects
        ).values_list('id', flat=True)
    )

    SavedCandidateSearch.objects.create(
        recruiter=request.user,
        skills=skills,
        location=location,
        projects=projects,
        seen_candidate_ids=matching_ids
    )

    messages.success(request, 'Candidate search saved.')
    return redirect('accounts.saved_searches')


@login_required
def saved_searches(request):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('home.index')

    searches = SavedCandidateSearch.objects.filter(
        recruiter=request.user
    ).order_by('-created_at')

    for search in searches:
        candidates = get_matching_candidates(
            search.skills,
            search.location,
            search.projects
        )

        seen_ids = set(search.seen_candidate_ids)

        search.new_candidates = [
            candidate for candidate in candidates
            if candidate.id not in seen_ids
        ]

        search.new_count = len(search.new_candidates)

    template_data = {
        'title': 'Saved Candidate Searches',
        'searches': searches,
    }

    return render(
        request,
        'accounts/saved_searches.html',
        {'template_data': template_data}
    )


@require_POST
@login_required
def mark_search_seen(request, search_id):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('home.index')

    search = get_object_or_404(
        SavedCandidateSearch,
        id=search_id,
        recruiter=request.user
    )

    current_ids = list(
        get_matching_candidates(
            search.skills,
            search.location,
            search.projects
        ).values_list('id', flat=True)
    )

    search.seen_candidate_ids = list(
        set(search.seen_candidate_ids) | set(current_ids)
    )
    search.save(update_fields=['seen_candidate_ids'])

    messages.success(request, 'New matches marked as seen.')
    return redirect('accounts.saved_searches')

