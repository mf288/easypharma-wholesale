from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from decimal import Decimal
import datetime
from wholesaleApp.models import (
    CustomerMaster,
    ProductMaster,
    ProductBatch,
    SalesInvoice,
    SalesInvoiceItem
)

# ==================== AJAX API ENDPOINTS ====================
# @login_required
def get_product_batches(request, pk):
    """API endpoint to get active batches with stock for a selected product."""
    batches = ProductBatch.objects.filter(product_id=pk, quantity__gt=0)
    data = []
    for b in batches:
        # Format MM/YY for display mask and YYYY-MM-DD for form submit
        exp_mask = b.expiry_date.strftime('%m/%y') if b.expiry_date else ''
        exp_real = b.expiry_date.strftime('%Y-%m-%d') if b.expiry_date else ''
        data.append({
            'id': b.id,
            'batch_number': b.batch_number,
            'expiry_mask': exp_mask,
            'expiry_real': exp_real,
            'mrp': float(b.mrp),
            'purchase_rate': float(b.purchase_rate),
            'sale_rate': float(b.sale_rate),
            'quantity': b.quantity
        })
    return JsonResponse(data, safe=False)


# ==================== SALES BILLING VIEWS ====================
# @login_required
def invoice_list(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not (has_feature_access(request.user, 'sales_create') or has_feature_access(request.user, 'sales_reprint')):
        messages.error(request, "Access Denied: You do not have permission to view Sales Invoices.")
        return redirect('home')
        
    invoices = SalesInvoice.objects.all().select_related('customer')
    context = {
        'invoices': invoices,
        'page_title': 'Sales Invoices (Retail Bills)',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'sale/invoice_list.html', context)

# @login_required
@transaction.atomic
def invoice_create(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'sales_create'):
        messages.error(request, "Access Denied: You do not have permission to create Sale Bills.")
        return redirect('home')
        
    customers = CustomerMaster.objects.filter(status=True, is_deleted=False)
    products = ProductMaster.objects.filter(status=True, is_deleted=False)
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        invoice_date = request.POST.get('invoice_date')
        gross_amount = Decimal(request.POST.get('gross_amount', 0))
        discount_amount = Decimal(request.POST.get('discount_amount', 0))
        gst_amount = Decimal(request.POST.get('gst_amount', 0))
        net_amount = Decimal(request.POST.get('net_amount', 0))
        
        # Extract item arrays
        product_ids = request.POST.getlist('product[]')
        batch_ids = request.POST.getlist('batch[]')
        sale_rates = request.POST.getlist('sale_rate[]')
        quantities = request.POST.getlist('quantity[]')
        free_quantities = request.POST.getlist('free_quantity[]')
        discounts = request.POST.getlist('discount_percentage[]')
        totals = request.POST.getlist('total_amount[]')
        
        # 1. Pre-validate stock availability for all items to avoid rollback errors
        for i in range(len(product_ids)):
            batch_id = batch_ids[i]
            qty = int(quantities[i])
            free_qty = int(free_quantities[i]) if free_quantities[i] else 0
            total_requested = qty + free_qty
            
            batch = get_object_or_404(ProductBatch, id=batch_id)
            if batch.quantity < total_requested:
                messages.error(request, f"Insufficient stock for {batch.product.name} (Batch: {batch.batch_number}). Available: {batch.quantity}, Requested: {total_requested}")
                return redirect('invoice_create')
        
        # Generate Invoice Number (INV-YYYYMMDD-ID)
        today_str = datetime.date.today().strftime('%Y%m%d')
        next_id = (SalesInvoice.objects.count() + 1)
        invoice_number = f"INV-{today_str}-{next_id:04d}"
        
        # 2. Create Sales Invoice
        invoice = SalesInvoice.objects.create(
            invoice_number=invoice_number,
            customer_id=customer_id,
            invoice_date=invoice_date,
            gross_amount=gross_amount,
            discount_amount=discount_amount,
            gst_amount=gst_amount,
            net_amount=net_amount,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # 3. Create items and deduct stock
        for i in range(len(product_ids)):
            prod_id = product_ids[i]
            batch_id = batch_ids[i]
            s_rate = Decimal(sale_rates[i])
            qty = int(quantities[i])
            free_qty = int(free_quantities[i]) if free_quantities[i] else 0
            disc_pct = Decimal(discounts[i]) if discounts[i] else Decimal('0.00')
            total_val = Decimal(totals[i])
            
            batch = ProductBatch.objects.get(id=batch_id)
            total_requested = qty + free_qty
            
            # Create Sales Invoice Item
            SalesInvoiceItem.objects.create(
                sales_invoice=invoice,
                product_id=prod_id,
                batch=batch,
                quantity=qty,
                free_quantity=free_qty,
                sale_rate=s_rate,
                discount_percentage=disc_pct,
                total_amount=total_val
            )
            
            # Deduct Batch Inventory stock
            batch.quantity -= total_requested
            batch.save()
            
        # 4. Update Customer Outstanding Balance (Accounts Receivable)
        customer = CustomerMaster.objects.get(id=customer_id)
        customer.opening_balance += invoice.net_amount
        customer.save()
        
        messages.success(request, f"Sales Invoice {invoice_number} saved. Stock deducted and customer balance updated.")
        return redirect('invoice_list')
        
    context = {
        'customers': customers,
        'products': products,
        'page_title': 'Create Sales Invoice (Bill)',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'sale/invoice_form.html', context)


def get_product_last_purchase_rate(request, pk):
    """API endpoint to get the actual last purchase rate for a selected product from history."""
    from wholesaleApp.views.security_helpers import has_feature_access
    if not (has_feature_access(request.user, 'view_margins') or has_feature_access(request.user, 'purchase_list')):
        return JsonResponse({'error': 'Permission Denied'}, status=403)

    from wholesaleApp.models.purchase import PurchaseEntryItem, ProductBatch
    
    last_item = PurchaseEntryItem.objects.filter(product_id=pk).select_related('purchase_entry').order_by('-purchase_entry__invoice_date', '-id').first()
    rate = 0.00
    if last_item:
        rate = float(last_item.purchase_rate)
    else:
        last_batch = ProductBatch.objects.filter(product_id=pk).order_by('-id').first()
        if last_batch:
            rate = float(last_batch.purchase_rate)
            
    return JsonResponse({'product_id': pk, 'last_purchase_rate': rate})
