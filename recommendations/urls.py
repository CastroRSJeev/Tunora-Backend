from django.urls import path
from .views import ai_recommend

urlpatterns = [
    path('recommend/', ai_recommend, name='ai-recommend'),
]
