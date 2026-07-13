from django.urls import path
from wholesaleApp.views.purchase_views import (
    po_list,
    po_create,
    purchase_entry_list,
    purchase_entry_create,
    get_product_details
)

urlpatterns = [
    # Purchase Orders
    path('purchase/order/list/', po_list, name='po_list'),
    path('purchase/order/create/', po_create, name='po_create'),

    # Purchase Entries
    path('purchase/entry/list/', purchase_entry_list, name='purchase_entry_list'),
    path('purchase/entry/create/', purchase_entry_create, name='purchase_entry_create'),

    # API endpoints
    path('api/product/<int:pk>/details/', get_product_details, name='api_product_details'),
]
