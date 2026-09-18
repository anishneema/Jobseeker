from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, CustomErrorList
from .models import RecruiterProfile


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
            return redirect('accounts.login')
        template_data['form'] = form
        return render(request, 'accounts/register.html',
                      {'template_data': template_data})


@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')
