from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import jobseeker_required
from .models import JobPosting, Application
from .forms import JobPostingForm, ApplicationForm


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