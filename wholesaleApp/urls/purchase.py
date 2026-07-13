from django.urls import path
from wholesaleApp.views.purchase_views import (
    purchase_list,
    purchase_create,
    purchase_edit,
    purchase_detail,
    purchase_delete,
    batch_stock_list,
)

urlpatterns = [
    # Purchase Entry URLs
    path('purchase/list/', purchase_list, name='purchase_list'),
    path('purchase/create/', purchase_create, name='purchase_create'),
    path('purchase/edit/<int:pk>/', purchase_edit, name='purchase_edit'),
    path('purchase/view/<int:pk>/', purchase_detail, name='purchase_detail'),
    path('purchase/delete/<int:pk>/', purchase_delete, name='purchase_delete'),

    # Batchwise Stock (auto-generated from purchase entries)
    path('purchase/batch-stock/', batch_stock_list, name='batch_stock_list'),
]
