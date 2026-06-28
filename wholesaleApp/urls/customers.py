from django.urls import path
from wholesaleApp.views.customers_views import (customer_list,customer_create)

urlpatterns = [
    path("customer/list/", customer_list, name='customerlist'),
    path("customer/create/", customer_create, name='createcustomer')

]