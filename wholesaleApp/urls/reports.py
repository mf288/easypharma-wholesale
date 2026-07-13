from django.urls import path
from wholesaleApp.views.reports_views import (
    reports_dashboard,
    report_sales,
    report_expiry,
    report_stock,
    report_outstanding
)

urlpatterns = [
    path('reports/dashboard/', reports_dashboard, name='reports_dashboard'),
    path('reports/sales/', report_sales, name='report_sales'),
    path('reports/expiry/', report_expiry, name='report_expiry'),
    path('reports/stock/', report_stock, name='report_stock'),
    path('reports/outstanding/', report_outstanding, name='report_outstanding'),
]
