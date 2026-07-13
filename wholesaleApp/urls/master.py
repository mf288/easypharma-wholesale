from django.urls import path
from wholesaleApp.views.master import HomeView, user_permission_matrix
from wholesaleApp.views.user_views import (
    user_list,
    user_create,
    user_edit,
    user_delete
)
from wholesaleApp.views.auth_views import user_login, user_logout


urlpatterns = [
    path('', HomeView, name='home'),
    path('settings/permissions/', user_permission_matrix, name='user_permission_matrix'),
    
    # User Authentication
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    # User Management CRUD
    path('settings/users/', user_list, name='user_list'),
    path('settings/users/create/', user_create, name='user_create'),
    path('settings/users/<int:pk>/edit/', user_edit, name='user_edit'),
    path('settings/users/<int:pk>/delete/', user_delete, name='user_delete'),
]
