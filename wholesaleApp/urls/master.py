from django.urls import path
from wholesaleApp.views import (HomeView)

urlpatterns = [
    path("home/", HomeView.as_view(), name='dashboard')
]
