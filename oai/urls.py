from django.urls import path
from . import views

urlpatterns = [
    path('ui/', views.ui), 
    path('chat_langchain/', views.chat_langchain), 
]