from django.urls import path
from wholesaleApp.views.customers_views import (
    customer_list,
    customer_create,
    customer_edit,
    customer_delete
)

urlpatterns = [
    path("customer/list/", customer_list, name='customer_list'),
    path("customer/create/", customer_create, name='createcustomer'),
    path("customer/edit/<int:pk>/", customer_edit, name='customer_edit'),
    path("customer/delete/<int:pk>/", customer_delete, name='customer_delete'),
]