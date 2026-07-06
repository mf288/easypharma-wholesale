from django.urls import path
from wholesaleApp.views.master import HomeView


urlpatterns = [
    path('', HomeView, name='home'),
]
