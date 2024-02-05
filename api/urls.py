from django.urls import path
from . import views

urlpatterns = [
  path('chatbot/', views.chatbot, name='chatbot'),
  path('register/', views.register, name='register'),
]