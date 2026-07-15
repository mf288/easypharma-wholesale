from django.urls import path
from wholesaleApp.views.sales_views import (
    invoice_list,
    invoice_create,
    invoice_print,
    get_product_batches,
    get_product_last_purchase_rate
)

urlpatterns = [
    # Sales Invoicing
    path('sales/invoice/list/', invoice_list, name='invoice_list'),
    path('sales/invoice/create/', invoice_create, name='invoice_create'),
    path('sales/invoice/<int:pk>/print/', invoice_print, name='invoice_print'),

    # API batch/rate fetchers
    path('api/product/<int:pk>/batches/', get_product_batches, name='api_product_batches'),
    path('api/product/<int:pk>/last-purchase/', get_product_last_purchase_rate, name='api_product_last_purchase'),
]
