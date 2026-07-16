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
    """Accounts Receivables and Payables outstanding ledgers with date and area filtering."""
    from wholesaleApp.views.security_helpers import has_feature_access
    if not has_feature_access(request.user, 'report_outstanding'):
        from django.contrib import messages
        messages.error(request, "Access Denied: You do not have permission to view Outstanding dues report.")
        return redirect('home')
        
    from django.db.models import Sum
    from django.utils import timezone
    from decimal import Decimal
    from wholesaleApp.models import CustomerPayment, PurchaseEntry, AreaMaster, SalesInvoice
    
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    area_id = request.GET.get('area')
    
    areas = AreaMaster.objects.filter(is_active=True).order_by('city')
    
    customers = []
    suppliers = []
    
    # 1. Process Customers
    customer_qs = CustomerMaster.objects.filter(is_deleted=False)
    if area_id:
        customer_qs = customer_qs.filter(area_id=area_id)
        
    if from_date and to_date:
        for c in customer_qs:
            credit_sales = SalesInvoice.objects.filter(
                customer=c, payment_type='Credit', invoice_date__range=[from_date, to_date]
            ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00')
            
            payments = CustomerPayment.objects.filter(
                customer=c, payment_date__range=[from_date, to_date]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            outstanding = credit_sales - payments
            if outstanding > 0:
                c.opening_balance = outstanding
                customers.append(c)
        customers.sort(key=lambda x: x.opening_balance, reverse=True)
    else:
        customers = list(customer_qs.filter(opening_balance__gt=0).order_by('-opening_balance'))
        
    # Calculate Aging (FIFO based on current filtered balance)
    today = timezone.now().date()
    for c in customers:
        bal = c.opening_balance
        invoices = SalesInvoice.objects.filter(customer=c, payment_type='Credit').order_by('-invoice_date', '-id')
        
        oldest_date = None
        accumulated = Decimal('0.00')
        for inv in invoices:
            accumulated += inv.net_amount
            oldest_date = inv.invoice_date
            if accumulated >= bal:
                break
                
        if oldest_date:
            c.oldest_date = oldest_date
            c.pending_days = (today - oldest_date).days
        else:
            c.oldest_date = c.created_at.date()
            c.pending_days = (today - c.created_at.date()).days
            
    # 2. Process Suppliers (suppliers do not belong to sales areas)
    if area_id:
        suppliers = []
    else:
        if from_date and to_date:
            all_suppliers = SupplierMaster.objects.filter(is_deleted=False)
            for s in all_suppliers:
                credit_purchases = PurchaseEntry.objects.filter(
                    supplier=s, payment_type='Credit', invoice_date__range=[from_date, to_date]
                ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00')
                
                outstanding = credit_purchases
                if outstanding > 0:
                    s.opening_balance = outstanding
                    suppliers.append(s)
            suppliers.sort(key=lambda x: x.opening_balance, reverse=True)
        else:
            suppliers = list(SupplierMaster.objects.filter(is_deleted=False, opening_balance__gt=0).order_by('-opening_balance'))
            
    total_receivable = sum(c.opening_balance for c in customers)
    total_payable = sum(s.opening_balance for s in suppliers)
    
    context = {
        'customers': customers,
        'suppliers': suppliers,
        'areas': areas,
        'selected_area': int(area_id) if area_id else None,
        'total_receivable': float(total_receivable),
        'total_payable': float(total_payable),
        'from_date': from_date,
        'to_date': to_date,
        'page_title': 'Outstanding Dues Ledger',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'reports/outstanding_report.html', context)
