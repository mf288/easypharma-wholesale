from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from decimal import Decimal
from wholesaleApp.models import (
    SupplierMaster,
    ProductMaster,
    ProductBatch,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseEntry,
    PurchaseEntryItem
)

# ==================== AJAX API ENDPOINTS ====================
# @login_required
def get_product_details(request, pk):
    """API endpoint to get product details like GST rate and packaging."""
    product = get_object_or_404(ProductMaster, pk=pk, is_deleted=False)
    data = {
        'id': product.id,
        'name': product.name,
        'pack_size': product.pack_size,
        'gst_rate': float(product.gst_rate),
        'hsn_code': product.hsn_code or ''
    }
    return JsonResponse(data)


# ==================== PURCHASE ORDER VIEWS ====================
# @login_required
def po_list(request):
    orders = PurchaseOrder.objects.all().select_related('supplier')
    context = {
        'orders': orders,
        'page_title': 'Purchase Orders'
    }
    return render(request, 'purchase/po_list.html', context)

# @login_required
@transaction.atomic
def po_create(request):
    suppliers = SupplierMaster.objects.filter(status=True, is_deleted=False)
    products = ProductMaster.objects.filter(status=True, is_deleted=False)
    
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        po_date = request.POST.get('po_date')
        po_number = request.POST.get('po_number')
        
        # Create Purchase Order
        po = PurchaseOrder.objects.create(
            po_number=po_number,
            supplier_id=supplier_id,
            po_date=po_date,
            status='Sent',
            created_by=request.user if request.user.is_authenticated else None
        )
        
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        expected_rates = request.POST.getlist('expected_rate[]')
        
        net_amount = Decimal('0.00')
        for i in range(len(product_ids)):
            prod_id = product_ids[i]
            qty = int(quantities[i])
            rate = Decimal(expected_rates[i])
            total = qty * rate
            net_amount += total
            
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product_id=prod_id,
                quantity=qty,
                expected_rate=rate,
                total_amount=total
            )
            
        po.net_amount = net_amount
        po.save()
        
        messages.success(request, f"Purchase Order {po_number} created and saved successfully!")
        return redirect('po_list')
        
    # Generate auto PO number (PO-YYYYMMDD-ID)
    import datetime
    today = datetime.date.today().strftime('%Y%m%d')
    next_id = (PurchaseOrder.objects.count() + 1)
    auto_po_number = f"PO-{today}-{next_id:04d}"
    
    context = {
        'suppliers': suppliers,
        'products': products,
        'auto_po_number': auto_po_number,
        'page_title': 'Create Purchase Order'
    }
    return render(request, 'purchase/po_form.html', context)


# ==================== PURCHASE ENTRY (INVOICE) VIEWS ====================
# @login_required
def purchase_entry_list(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not (has_feature_access(request.user, 'purchase_list') or has_feature_access(request.user, 'purchase_create')):
        messages.error(request, "Access Denied: You do not have permission to view Purchase Entries.")
        return redirect('home')
        
    entries = PurchaseEntry.objects.all().select_related('supplier')
    context = {
        'entries': entries,
        'page_title': 'Purchase Entries (Supplier Bills)',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'purchase/entry_list.html', context)

# @login_required
@transaction.atomic
def purchase_entry_create(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'purchase_create'):
        messages.error(request, "Access Denied: You do not have permission to record Purchase Entries.")
        return redirect('home')
        
    suppliers = SupplierMaster.objects.filter(status=True, is_deleted=False)
    products = ProductMaster.objects.filter(status=True, is_deleted=False)
    
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        invoice_number = request.POST.get('invoice_number')
        invoice_date = request.POST.get('invoice_date')
        gross_amount = Decimal(request.POST.get('gross_amount', 0))
        discount_amount = Decimal(request.POST.get('discount_amount', 0))
        gst_amount = Decimal(request.POST.get('gst_amount', 0))
        net_amount = Decimal(request.POST.get('net_amount', 0))
        
        # Create the purchase entry
        entry = PurchaseEntry.objects.create(
            supplier_id=supplier_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            gross_amount=gross_amount,
            discount_amount=discount_amount,
            gst_amount=gst_amount,
            net_amount=net_amount,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Extract item rows
        product_ids = request.POST.getlist('product[]')
        batches = request.POST.getlist('batch_number[]')
        expiries = request.POST.getlist('expiry_date[]')
        mrps = request.POST.getlist('mrp[]')
        p_rates = request.POST.getlist('purchase_rate[]')
        s_rates = request.POST.getlist('sale_rate[]')
        quantities = request.POST.getlist('quantity[]')
        free_quantities = request.POST.getlist('free_quantity[]')
        discounts = request.POST.getlist('discount_percentage[]')
        totals = request.POST.getlist('total_amount[]')
        
        for i in range(len(product_ids)):
            prod_id = product_ids[i]
            batch_no = batches[i]
            exp_date = expiries[i]
            mrp_val = Decimal(mrps[i])
            pr_val = Decimal(p_rates[i])
            sr_val = Decimal(s_rates[i])
            qty = int(quantities[i])
            free_qty = int(free_quantities[i]) if free_quantities[i] else 0
            disc_pct = Decimal(discounts[i]) if discounts[i] else Decimal('0.00')
            total_val = Decimal(totals[i])
            
            # 1. Create Purchase Entry Item
            PurchaseEntryItem.objects.create(
                purchase_entry=entry,
                product_id=prod_id,
                batch_number=batch_no,
                expiry_date=exp_date,
                mrp=mrp_val,
                purchase_rate=pr_val,
                sale_rate=sr_val,
                quantity=qty,
                free_quantity=free_qty,
                discount_percentage=disc_pct,
                total_amount=total_val
            )
            
            # 2. Update/Create Batch Inventory Stock
            batch, created = ProductBatch.objects.get_or_create(
                product_id=prod_id,
                batch_number=batch_no,
                expiry_date=exp_date,
                mrp=mrp_val,
                purchase_rate=pr_val,
                sale_rate=sr_val,
                defaults={'quantity': 0}
            )
            batch.quantity += (qty + free_qty)
            batch.save()
            
        # 3. Update Supplier balance (Add to outstanding accounts payable)
        supplier = SupplierMaster.objects.get(id=supplier_id)
        supplier.opening_balance += entry.net_amount
        supplier.save()
        
        messages.success(request, f"Purchase Entry recorded successfully! Stock added for {len(product_ids)} items.")
        return redirect('purchase_entry_list')
        
    context = {
        'suppliers': suppliers,
        'products': products,
        'page_title': 'Add Purchase Entry (Supplier Bill)',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'purchase/entry_form.html', context)
