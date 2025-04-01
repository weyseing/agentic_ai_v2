from django.urls import path
from . import views

urlpatterns = [
    path('ui/', views.ui), 
    path('chat/', views.chat), 
]