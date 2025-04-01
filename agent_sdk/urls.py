from django.urls import path
from . import views

urlpatterns = [
    path('ui/', views.ui), 
    path('response_api/', views.response_api), 
    path('agent_sdk/', views.agent_sdk),
    path('agent_sdk_stream/', views.agent_sdk_stream),
    path('async_call/', views.async_call),
]