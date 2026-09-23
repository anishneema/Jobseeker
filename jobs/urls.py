from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='jobs.index'),
    path('post/', views.post, name='jobs.post'),
    path('mine/', views.mine, name='jobs.mine'),
    path('applications/<int:id>/', views.application_detail, name='jobs.application_detail'),
    path('<int:id>/', views.show, name='jobs.show'),
    path('<int:id>/edit/', views.edit, name='jobs.edit'),
    
]
