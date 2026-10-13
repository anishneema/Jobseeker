from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='messaging.inbox'),
    path('compose/<int:user_id>/', views.compose, name='messaging.compose'),
    path('<int:id>/', views.detail, name='messaging.detail'),
]
