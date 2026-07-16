from django.urls import path
from wholesaleApp.views.purchase_views import (
    po_list,
    po_create,
    purchase_entry_list,
    purchase_entry_create,
    purchase_entry_edit,
    purchase_entry_delete,
    get_product_details
)

urlpatterns = [
    # Purchase Orders
    path('purchase/order/list/', po_list, name='po_list'),
    path('purchase/order/create/', po_create, name='po_create'),

    # Purchase Entries
    path('purchase/entry/list/', purchase_entry_list, name='purchase_entry_list'),
    path('purchase/entry/create/', purchase_entry_create, name='purchase_entry_create'),
    path('purchase/entry/<int:pk>/edit/', purchase_entry_edit, name='purchase_entry_edit'),
    path('purchase/entry/<int:pk>/delete/', purchase_entry_delete, name='purchase_entry_delete'),

    # API endpoints
    path('api/product/<int:pk>/details/', get_product_details, name='api_product_details'),
]
