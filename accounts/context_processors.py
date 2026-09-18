def role(request):
    is_recruiter = False
    is_seeker = False
    if request.user.is_authenticated:
        is_recruiter = hasattr(request.user, 'recruiter_profile')
        is_seeker = hasattr(request.user, 'jobseeker_profile')
    return {'is_recruiter': is_recruiter, 'is_seeker': is_seeker}
