from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='jobs.index'),
    path('post/', views.post, name='jobs.post'),
    path('mine/', views.mine, name='jobs.mine'),
    path('<int:id>/applications/', views.job_applications, name='jobs.job_applications'),
    path('applications/mine/', views.my_applications, name='jobs.my_applications'),
    path('applications/<int:id>/', views.application_detail, name='jobs.application_detail'),
    path('<int:id>/', views.show, name='jobs.show'),
    path('<int:id>/edit/', views.edit, name='jobs.edit'),
    path('<int:id>/apply/', views.apply, name='jobs.apply'),
]