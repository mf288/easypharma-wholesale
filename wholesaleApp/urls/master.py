from django.urls import path
from wholesaleApp.views.master import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('home/', HomeView.as_view(), name='dashboard'),
]
