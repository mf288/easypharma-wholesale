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
            'wholesale_rate': float(b.wholesale_rate),
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
    print_invoice_id = request.session.pop('print_invoice_id', None)
    context = {
        'invoices': invoices,
        'page_title': 'Sales Invoices (Retail Bills)',
        'user_perms': get_user_permissions_context(request.user),
        'print_invoice_id': print_invoice_id
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
        payment_type = request.POST.get('payment_type', 'Credit')
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
            payment_type=payment_type,
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
        if payment_type == 'Credit':
            customer = CustomerMaster.objects.get(id=customer_id)
            customer.opening_balance += invoice.net_amount
            customer.save()
        
        messages.success(request, f"Sales Invoice {invoice_number} saved. Stock deducted and customer balance updated.")
        request.session['print_invoice_id'] = invoice.id
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


def number_to_words(number):
    """Simple helper to convert a number to Indian currency format words."""
    try:
        number = int(round(number))
        if number == 0:
            return "Rupees Zero Only"
        
        words = []
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                 "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        def helper(n):
            if n < 20:
                return units[n]
            elif n < 100:
                return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")
            elif n < 1000:
                return units[n // 100] + " Hundred" + (" and " + helper(n % 100) if n % 100 != 0 else "")
            
        # Break into crores, lakhs, thousands, hundreds
        crore = number // 10000000
        number %= 10000000
        lakh = number // 100000
        number %= 100000
        thousand = number // 1000
        number %= 1000
        
        if crore:
            words.append(helper(crore) + " Crore")
        if lakh:
            words.append(helper(lakh) + " Lakh")
        if thousand:
            words.append(helper(thousand) + " Thousand")
        if number:
            words.append(helper(number))
            
        return "Rupees " + " ".join(words) + " Only"
    except Exception:
        return ""


# @login_required
def invoice_print(request, pk):
    """View to render the printable invoice styled for A4 half-page (A5 landscape)."""
    # Fetch invoice, filtering by tenant is handled automatically by the custom TenantManager
    invoice = get_object_or_404(SalesInvoice, id=pk)
    items = invoice.items.all().select_related('product', 'batch')
    
    # Identify tenant details to print.
    # Fallback to the invoice's own tenant if request.tenant is None (Admin mode)
    print_tenant = request.tenant or invoice.tenant
    
    # Calculate invoice items breakdown
    item_details = []
    total_taxable_value = 0
    total_gst_calculated = 0
    
    for idx, item in enumerate(items, 1):
        qty = item.quantity
        rate = item.sale_rate
        disc_pct = item.discount_percentage
        gst_pct = item.product.gst_rate
        
        base_val = qty * rate
        disc_val = base_val * (disc_pct / 100)
        taxable_val = base_val - disc_val
        gst_val = taxable_val * (gst_pct / 100)
        
        total_taxable_value += taxable_val
        total_gst_calculated += gst_val
        
        # Calculate split taxes (CGST and SGST are 50% each of total GST for local sales)
        cgst_pct = gst_pct / 2
        sgst_pct = gst_pct / 2
        cgst_val = gst_val / 2
        sgst_val = gst_val / 2
        
        item_details.append({
            'idx': idx,
            'item': item,
            'product_name': item.product.name,
            'pack_size': item.product.pack_size,
            'hsn_code': item.product.hsn_code,
            'batch_number': item.batch.batch_number,
            'expiry_mask': item.batch.expiry_date.strftime('%m/%y') if item.batch.expiry_date else '—',
            'qty': qty,
            'free_qty': item.free_quantity,
            'mrp': item.batch.mrp,
            'rate': rate,
            'disc_pct': disc_pct,
            'gst_pct': gst_pct,
            'cgst_pct': cgst_pct,
            'sgst_pct': sgst_pct,
            'cgst_val': cgst_val,
            'sgst_val': sgst_val,
            'amount': item.total_amount
        })
        
    net_amount_words = number_to_words(invoice.net_amount)
    
    context = {
        'invoice': invoice,
        'customer': invoice.customer,
        'tenant': print_tenant,
        'item_details': item_details,
        'total_taxable_value': total_taxable_value,
        'total_gst_calculated': total_gst_calculated,
        'cgst_total': total_gst_calculated / 2,
        'sgst_total': total_gst_calculated / 2,
        'net_amount_words': net_amount_words
    }
    return render(request, 'sale/invoice_print.html', context)


# @login_required
@transaction.atomic
def invoice_edit(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'sales_create'):
        messages.error(request, "Access Denied: You do not have permission to edit Sale Bills.")
        return redirect('invoice_list')
        
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    customers = CustomerMaster.objects.filter(status=True, is_deleted=False)
    products = ProductMaster.objects.filter(status=True, is_deleted=False)
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        invoice_date = request.POST.get('invoice_date')
        payment_type = request.POST.get('payment_type', 'Credit')
        gross_amount = Decimal(request.POST.get('gross_amount', 0))
        discount_amount = Decimal(request.POST.get('discount_amount', 0))
        gst_amount = Decimal(request.POST.get('gst_amount', 0))
        net_amount = Decimal(request.POST.get('net_amount', 0))
        
        # Extract item arrays from POST
        product_ids = request.POST.getlist('product[]')
        batch_ids = request.POST.getlist('batch[]')
        sale_rates = request.POST.getlist('sale_rate[]')
        quantities = request.POST.getlist('quantity[]')
        free_quantities = request.POST.getlist('free_quantity[]')
        discounts = request.POST.getlist('discount_percentage[]')
        totals = request.POST.getlist('total_amount[]')
        
        # 1. Temporarily restore all old stock quantities to calculate inventory correctly
        old_items = list(invoice.items.all().select_related('batch'))
        for item in old_items:
            batch = item.batch
            batch.quantity += (item.quantity + item.free_quantity)
            batch.save()
            
        # 2. Check if new items have sufficient stock
        for i in range(len(product_ids)):
            batch_id = batch_ids[i]
            qty = int(quantities[i])
            free_qty = int(free_quantities[i]) if free_quantities[i] else 0
            
            batch = ProductBatch.objects.get(id=batch_id)
            if batch.quantity < (qty + free_qty):
                # Rollback temporary stock changes by restoring them back to old state
                for old_item in old_items:
                    obatch = old_item.batch
                    obatch.quantity -= (old_item.quantity + old_item.free_quantity)
                    obatch.save()
                messages.error(request, f"Insufficient stock for batch {batch.batch_number}! Available: {batch.quantity}")
                return redirect('invoice_edit', pk=pk)
                
        # 3. Update customer outstanding balance: revert old net amount
        if invoice.payment_type == 'Credit':
            old_customer = invoice.customer
            old_customer.opening_balance -= invoice.net_amount
            old_customer.save()
        
        # 4. Delete old invoice items
        invoice.items.all().delete()
        
        # 5. Save updated invoice headers
        invoice.customer_id = customer_id
        invoice.invoice_date = invoice_date
        invoice.payment_type = payment_type
        invoice.gross_amount = gross_amount
        invoice.discount_amount = discount_amount
        invoice.gst_amount = gst_amount
        invoice.net_amount = net_amount
        invoice.save()
        
        # 6. Save new items and deduct stock
        for i in range(len(product_ids)):
            prod_id = product_ids[i]
            batch_id = batch_ids[i]
            s_rate = Decimal(sale_rates[i])
            qty = int(quantities[i])
            free_qty = int(free_quantities[i]) if free_quantities[i] else 0
            disc_pct = Decimal(discounts[i]) if discounts[i] else Decimal('0.00')
            total_val = Decimal(totals[i])
            
            batch = ProductBatch.objects.get(id=batch_id)
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
            # Deduct stock
            batch.quantity -= (qty + free_qty)
            batch.save()
            
        # 7. Apply new invoice net amount to customer balance
        if payment_type == 'Credit':
            new_customer = invoice.customer
            new_customer.opening_balance += invoice.net_amount
            new_customer.save()
        
        messages.success(request, f"Invoice {invoice.invoice_number} updated successfully!")
        request.session['print_invoice_id'] = invoice.id
        return redirect('invoice_list')
        
    context = {
        'invoice': invoice,
        'customers': customers,
        'products': products,
        'page_title': f'Edit Sales Invoice {invoice.invoice_number}',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'sale/invoice_edit.html', context)


# @login_required
@transaction.atomic
def invoice_delete(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access
    if not has_feature_access(request.user, 'sales_create'):
        messages.error(request, "Access Denied: You do not have permission to delete/cancel Sale Bills.")
        return redirect('invoice_list')
        
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    
    # 1. Restore inventory stock
    for item in invoice.items.all().select_related('batch'):
        batch = item.batch
        batch.quantity += (item.quantity + item.free_quantity)
        batch.save()
        
    # 2. Subtract from customer outstanding balance
    if invoice.payment_type == 'Credit':
        customer = invoice.customer
        customer.opening_balance -= invoice.net_amount
        customer.save()
    
    # 3. Delete the invoice
    invoice_number = invoice.invoice_number
    invoice.delete()
    
    messages.success(request, f"Invoice {invoice_number} has been deleted successfully, stock restored and customer balance reverted.")
    return redirect('invoice_list')
