from django.urls import path
from wholesaleApp.views.customers_views import (
    customer_list,
    customer_create,
    customer_edit,
    customer_delete,
    area_list,
    area_create,
    area_edit,
    area_delete,
    subarea_create,
    subarea_edit,
    subarea_delete
)

urlpatterns = [
    path("customer/list/", customer_list, name='customer_list'),
    path("customer/create/", customer_create, name='createcustomer'),
    path("customer/edit/<int:pk>/", customer_edit, name='customer_edit'),
    path("customer/delete/<int:pk>/", customer_delete, name='customer_delete'),
    
    # Area Master
    path("area/list/", area_list, name='area_list'),
    path("area/create/", area_create, name='area_create'),
    path("area/edit/<int:pk>/", area_edit, name='area_edit'),
    path("area/delete/<int:pk>/", area_delete, name='area_delete'),
    
    # Subarea Master
    path("subarea/create/", subarea_create, name='subarea_create'),
    path("subarea/edit/<int:pk>/", subarea_edit, name='subarea_edit'),
    path("subarea/delete/<int:pk>/", subarea_delete, name='subarea_delete'),
]