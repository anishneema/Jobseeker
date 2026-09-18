from django.shortcuts import render


def index(request):
    template_data = {}
    template_data['title'] = 'JobSeeker'
    return render(request, 'home/index.html',
                  {'template_data': template_data})
