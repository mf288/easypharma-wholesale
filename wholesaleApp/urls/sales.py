from django.urls import path
from wholesaleApp.views.sales_views import (
    invoice_list,
    invoice_create,
    get_product_batches,
    get_product_last_purchase_rate
)

urlpatterns = [
    # Sales Invoicing
    path('sales/invoice/list/', invoice_list, name='invoice_list'),
    path('sales/invoice/create/', invoice_create, name='invoice_create'),

    # API batch/rate fetchers
    path('api/product/<int:pk>/batches/', get_product_batches, name='api_product_batches'),
    path('api/product/<int:pk>/last-purchase/', get_product_last_purchase_rate, name='api_product_last_purchase'),
]
