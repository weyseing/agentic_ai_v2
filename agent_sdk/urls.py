from django.urls import path
from . import views

urlpatterns = [
    path('ui/', views.ui), 
    path('response_api/', views.response_api), 
    path('agent_sdk/', views.agent_sdk), 
]