from django.shortcuts import render, redirect
from django.db.models import Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from wholesaleApp.models import (
    SalesInvoice,
    SalesInvoiceItem,
    ProductBatch,
    CustomerMaster,
    SupplierMaster
)
from wholesaleApp.views.security_helpers import get_user_permissions_context

# ==================== REPORTS MODULE VIEWS ====================

def reports_dashboard(request):
    """Main Reports Hub listing all available reports."""
    context = {
        'page_title': 'Enterprise Wholesale Reports Hub',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'reports/dashboard.html', context)


def report_sales(request):
    """Sales & GST Tax reporting with date filters."""
    today = timezone.now().date()
    
    # Date filter range (default current month)
    start_date_str = request.GET.get('start_date', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    invoices = SalesInvoice.objects.filter(invoice_date__range=[start_date, end_date]).select_related('customer')
    
    # Aggregates
    totals = invoices.aggregate(
        gross=Sum('gross_amount'),
        discount=Sum('discount_amount'),
        gst=Sum('gst_amount'),
        net=Sum('net_amount')
    )
    
    context = {
        'invoices': invoices,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'totals': totals,
        'page_title': 'GST Sales Summary Report',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'reports/sales_report.html', context)


def report_expiry(request):
    """Pharmaceutical Expiry alerts and shelf-life tracking."""
    today = timezone.now().date()
    
    # Expiry limit filter in days (default 90 days)
    days_limit = int(request.GET.get('days', '90'))
    limit_date = today + timedelta(days=days_limit)
    
    batches = ProductBatch.objects.filter(
        expiry_date__lte=limit_date, 
        quantity__gt=0
    ).select_related('product').order_by('expiry_date')
    
    report_data = []
    for b in batches:
        days_left = (b.expiry_date - today).days
        report_data.append({
            'product': b.product.name,
            'pack': b.product.pack_size,
            'batch_number': b.batch_number,
            'stock': b.quantity,
            'expiry_date': b.expiry_date,
            'days_left': days_left,
            'mrp': float(b.mrp),
            'purchase_rate': float(b.purchase_rate),
            'loss_value': float(b.quantity * b.purchase_rate)
        })
        
    context = {
        'batches': report_data,
        'days': days_limit,
        'page_title': 'Pharma Expiry Alert Report',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'reports/expiry_report.html', context)


def report_stock(request):
    """Current Stock levels and valuation audit reporting."""
    batches = ProductBatch.objects.filter(quantity__gt=0).select_related('product')
    
    report_data = []
    total_qty = 0
    total_purchase_val = 0.00
    total_sale_val = 0.00
    
    for b in batches:
        p_val = float(b.quantity * b.purchase_rate)
        s_val = float(b.quantity * b.sale_rate)
        total_qty += b.quantity
        total_purchase_val += p_val
        total_sale_val += s_val
        
        report_data.append({
            'product': b.product.name,
            'pack': b.product.pack_size,
            'batch_number': b.batch_number,
            'stock': b.quantity,
            'purchase_rate': float(b.purchase_rate),
            'sale_rate': float(b.sale_rate),
            'purchase_val': p_val,
            'sale_val': s_val
        })
        
    context = {
        'batches': report_data,
        'total_qty': total_qty,
        'total_purchase_val': total_purchase_val,
        'total_sale_val': total_sale_val,
        'page_title': 'Current Stock Valuation Report',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'reports/stock_valuation.html', context)


def report_outstanding(request):
    """Accounts Receivables and Payables outstanding ledgers."""
    # Customers dues
    customers = CustomerMaster.objects.filter(is_deleted=False, opening_balance__gt=0).order_by('-opening_balance')
    total_receivable = customers.aggregate(total=Sum('opening_balance'))['total'] or Decimal(0.00)
    
    # Suppliers dues
    suppliers = SupplierMaster.objects.filter(is_deleted=False, opening_balance__gt=0).order_by('-opening_balance')
    total_payable = suppliers.aggregate(total=Sum('opening_balance'))['total'] or Decimal(0.00)
    
    context = {
        'customers': customers,
        'suppliers': suppliers,
        'total_receivable': float(total_receivable),
        'total_payable': float(total_payable),
        'page_title': 'Outstanding Dues Ledger',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'reports/outstanding_report.html', context)
