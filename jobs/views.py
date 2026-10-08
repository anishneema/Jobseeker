from functools import wraps
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import jobseeker_required
from .models import JobPosting, Application, CartItem
from .forms import JobPostingForm, ApplicationForm
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def _map_payload(jobs):
    payload = []
    for job in jobs:
        if job.latitude is None or job.longitude is None:
            continue
        payload.append({
            'id': job.id,
            'title': job.title,
            'location': job.location,
            'salary': job.salary_range(),
            'lat': float(job.latitude),
            'lng': float(job.longitude),
            'url': reverse('jobs.show', args=[job.id]),
        })
    return payload

COMMUTE_RADIUS_CHOICES = (5, 10, 25, 50)


def _saved_commute(user):
    if not (user.is_authenticated and hasattr(user, 'jobseeker_profile')):
        return None
    profile = user.jobseeker_profile
    if (profile.commute_radius_miles is None
            or profile.home_latitude is None
            or profile.home_longitude is None):
        return None
    return {
        'miles': profile.commute_radius_miles,
        'lat': float(profile.home_latitude),
        'lng': float(profile.home_longitude),
    }

def recruiter_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'recruiter_profile'):
            messages.error(request, 'Only recruiters can manage job postings.')
            return redirect('jobs.index')
        return view_func(request, *args, **kwargs)
    return wrapper


def index(request):
    jobs = JobPosting.objects.filter(status='open')
    title = request.GET.get('title', '').strip()
    skills = request.GET.get('skills', '').strip()
    location = request.GET.get('location', '').strip()
    salary_min = request.GET.get('salary_min', '').strip()
    salary_max = request.GET.get('salary_max', '').strip()
    remote_onsite = request.GET.get('remote_onsite', '').strip()
    visa_sponsorship = request.GET.get('visa_sponsorship', '').strip()

    if title:
        jobs = jobs.filter(title__icontains=title)
    if skills:
        jobs = jobs.filter(skills_required__icontains=skills)
    if location:
        jobs = jobs.filter(location__icontains=location)
    try:
        if salary_min:
            jobs = jobs.filter(salary_max__gte=int(salary_min))
        if salary_max:
            jobs = jobs.filter(salary_min__lte=int(salary_max))
    except ValueError:
        pass
    if remote_onsite:
        jobs = jobs.filter(remote_onsite=remote_onsite)
    if visa_sponsorship == 'yes':
        jobs = jobs.filter(visa_sponsorship=True)
    elif visa_sponsorship == 'no':
        jobs = jobs.filter(visa_sponsorship=False)

    template_data = {}
    template_data['title'] = 'Search Jobs'
    template_data['jobs'] = jobs
    template_data['filters'] = {
        'title': title,
        'skills': skills,
        'location': location,
        'salary_min': salary_min,
        'salary_max': salary_max,
        'remote_onsite': remote_onsite,
        'visa_sponsorship': visa_sponsorship,
    }
    if request.user.is_authenticated and hasattr(request.user, 'jobseeker_profile'):
        template_data['cart_job_ids'] = set(CartItem.objects.filter(
            jobseeker=request.user
        ).values_list('job_id', flat=True))
    template_data['map_jobs'] = _map_payload(jobs)
    template_data['commute'] = _saved_commute(request.user)
    template_data['map_view'] = request.GET.get('view') == 'map'
    template_data['maps_api_key'] = settings.GOOGLE_MAPS_API_KEY

    return render(request, 'jobs/job_list.html',
                  {'template_data': template_data})


def show(request, id):
    job = get_object_or_404(JobPosting, id=id)
    template_data = {}
    template_data['title'] = job.title
    template_data['job'] = job
    template_data['is_owner'] = (
        request.user.is_authenticated and job.recruiter_id == request.user.id
    )
    if request.user.is_authenticated and hasattr(request.user, 'jobseeker_profile'):
        template_data['application'] = Application.objects.filter(
            job=job, applicant=request.user
        ).first()
        template_data['application_form'] = ApplicationForm()
        template_data['in_cart'] = CartItem.objects.filter(
            job=job, jobseeker=request.user
        ).exists()
    return render(request, 'jobs/job_detail.html',
                  {'template_data': template_data})


@jobseeker_required
def apply(request, id):
    job = get_object_or_404(JobPosting, id=id)
    if request.method != 'POST':
        return redirect('jobs.show', id=job.id)
    if job.status != 'open':
        messages.error(request, 'This job is no longer accepting applications.')
        return redirect('jobs.show', id=job.id)
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.error(request, 'You have already applied to this job.')
        return redirect('jobs.show', id=job.id)
    form = ApplicationForm(request.POST)
    if form.is_valid():
        application = form.save(commit=False)
        application.job = job
        application.applicant = request.user
        application.save()
        messages.success(request, 'Application submitted.')
    else:
        messages.error(request, 'Could not submit your application.')
    return redirect('jobs.show', id=job.id)


@recruiter_required
def post(request):
    template_data = {}
    template_data['title'] = 'Post a Job'
    template_data['maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
    if request.method == 'GET':
        template_data['form'] = JobPostingForm()
        return render(request, 'jobs/post_job.html',
                      {'template_data': template_data})
    form = JobPostingForm(request.POST)
    if form.is_valid():
        job = form.save(commit=False)
        job.recruiter = request.user
        job.save()
        messages.success(request, 'Job posting created.')
        return redirect('jobs.show', id=job.id)
    template_data['form'] = form
    return render(request, 'jobs/post_job.html',
                  {'template_data': template_data})


@recruiter_required
def edit(request, id):
    job = get_object_or_404(JobPosting, id=id, recruiter=request.user)
    template_data = {}
    template_data['title'] = 'Edit Job'
    template_data['job'] = job
    template_data['maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
    if request.method == 'GET':
        template_data['form'] = JobPostingForm(instance=job)
        return render(request, 'jobs/post_job.html',
                      {'template_data': template_data})
    form = JobPostingForm(request.POST, instance=job)
    if form.is_valid():
        form.save()
        messages.success(request, 'Job posting updated.')
        return redirect('jobs.show', id=job.id)
    template_data['form'] = form
    return render(request, 'jobs/post_job.html',
                  {'template_data': template_data})


@recruiter_required
def mine(request):
    template_data = {}
    template_data['title'] = 'My Jobs'
    template_data['jobs'] = JobPosting.objects.filter(recruiter=request.user)
    return render(request, 'jobs/my_jobs.html',
                  {'template_data': template_data})
@recruiter_required
def application_detail(request, id):

    application = get_object_or_404(
        Application,
        id=id,
        job__recruiter=request.user
    )

    profile = application.applicant.jobseeker_profile

    template_data = {
        'title': 'Candidate Application',
        'application': application,
        'profile': profile,
        'show_skills': profile.show_skills and bool(profile.skills),
        'show_education': profile.show_education and bool(profile.education),
        'show_work_experience': (profile.show_work_experience and bool(profile.work_experience)),
    }

    return render(
        request,
        'jobs/application_detail.html',
        {'template_data': template_data}
    )


@jobseeker_required
def my_applications(request):
    template_data = {}
    template_data['title'] = 'My Applications'
    template_data['applications'] = Application.objects.filter(
        applicant=request.user
    ).select_related('job', 'job__recruiter')
    return render(request, 'jobs/my_applications.html',
                  {'template_data': template_data})

@recruiter_required
def job_applications(request, id):
    job = get_object_or_404(
        JobPosting,
        id=id,
        recruiter=request.user
    )

    applications = Application.objects.filter(
        job=job
    ).select_related('applicant')

    template_data = {
        'title': 'Job Applications',
        'job': job,
        'applications': applications,
    }

    return render(
        request,
        'jobs/job_applications.html',
        {'template_data': template_data}
    )

def _safe_next(request, fallback):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return next_url
    return fallback

@jobseeker_required
def recommendations(request):
    profile = request.user.jobseeker_profile
    candidate_skills = {
        s.strip().lower() for s in profile.skills.split(',') if s.strip()
    }
    applied_job_ids = Application.objects.filter(
        applicant=request.user
    ).values_list('job_id', flat=True)

    scored_jobs = []
    if candidate_skills:
        open_jobs = JobPosting.objects.filter(
            status='open'
        ).exclude(id__in=applied_job_ids)
        for job in open_jobs:
            job_skills = {
                s.strip().lower() for s in job.skills_required.split(',') if s.strip()
            }
            matched = candidate_skills & job_skills
            if matched:
                scored_jobs.append({
                    'job': job,
                    'matched_skills': sorted(matched),
                    'match_count': len(matched),
                })
        scored_jobs.sort(key=lambda entry: entry['match_count'], reverse=True)

    template_data = {
        'title': 'Recommended for You',
        'scored_jobs': scored_jobs,
        'has_skills': bool(candidate_skills),
    }
    return render(request, 'jobs/recommendations.html',
                  {'template_data': template_data})


@jobseeker_required
def cart(request):
    items = CartItem.objects.filter(
        jobseeker=request.user
    ).select_related('job', 'job__recruiter')
    applied_job_ids = set(Application.objects.filter(
        applicant=request.user
    ).values_list('job_id', flat=True))

    template_data = {
        'title': 'My Cart',
        'items': items,
        'applied_job_ids': applied_job_ids,
    }
    return render(request, 'jobs/cart.html', {'template_data': template_data})


@jobseeker_required
def cart_add(request, id):
    job = get_object_or_404(JobPosting, id=id)
    if request.method != 'POST':
        return redirect('jobs.show', id=job.id)
    CartItem.objects.get_or_create(jobseeker=request.user, job=job)
    messages.success(request, f'Added "{job.title}" to your cart.')
    return redirect(_safe_next(request, reverse('jobs.show', args=[job.id])))


@jobseeker_required
def cart_remove(request, id):
    item = get_object_or_404(CartItem, id=id, jobseeker=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Removed from your cart.')
    return redirect(_safe_next(request, reverse('jobs.cart')))

@jobseeker_required
def commute_save(request):
    fallback = reverse('jobs.index') + '?view=map'
    if request.method != 'POST':
        return redirect(fallback)
    profile = request.user.jobseeker_profile
    if request.POST.get('clear'):
        profile.commute_radius_miles = None
        profile.home_latitude = None
        profile.home_longitude = None
        profile.save()
        messages.success(request, 'Commute preference cleared.')
        return redirect(_safe_next(request, fallback))
    try:
        miles = int(request.POST.get('miles', ''))
        lat = float(request.POST.get('lat', ''))
        lng = float(request.POST.get('lng', ''))
    except ValueError:
        miles = lat = lng = None
    if (miles not in COMMUTE_RADIUS_CHOICES
            or lat is None or not (-90 <= lat <= 90)
            or not (-180 <= lng <= 180)):
        messages.error(
            request,
            'Click the map to mark where you are and choose a distance before saving.'
        )
        return redirect(_safe_next(request, fallback))
    profile.commute_radius_miles = miles
    profile.home_latitude = round(lat, 6)
    profile.home_longitude = round(lng, 6)
    profile.save()
    messages.success(request, f'Saved: only showing jobs within {miles} miles on the map.')
    return redirect(_safe_next(request, fallback))