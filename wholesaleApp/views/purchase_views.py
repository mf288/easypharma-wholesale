from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from wholesaleApp.models import (
    PurchaseMaster,
    PurchaseItem,
    BatchStock,
    SupplierMaster,
    ProductMaster,
)


# ==================== HELPERS ====================
def _to_decimal(value, default='0'):
    try:
        return Decimal(str(value)) if value not in (None, '') else Decimal(default)
    except InvalidOperation:
        return Decimal(default)


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sync_batch_stock(product_id, batch_number, expiry_date):
    """
    Recalculate the BatchStock row for a given product + batch + expiry
    combination, based on all active (non-deleted) purchase entries.
    Called after every purchase create / edit / delete so that batchwise
    stock always reflects the current state of purchase entries.
    """
    active_items = PurchaseItem.objects.filter(
        product_id=product_id,
        batch_number=batch_number,
        expiry_date=expiry_date,
        purchase__is_deleted=False,
    ).select_related('purchase').order_by('purchase__invoice_date', 'id')

    total_qty = 0
    latest_item = None
    for item in active_items:
        total_qty += item.quantity + item.free_quantity
        latest_item = item  # last one (most recent invoice_date) wins for rate/mrp

    if total_qty <= 0 or latest_item is None:
        BatchStock.objects.filter(
            product_id=product_id, batch_number=batch_number, expiry_date=expiry_date
        ).delete()
        return

    stock, created = BatchStock.objects.get_or_create(
        product_id=product_id,
        batch_number=batch_number,
        expiry_date=expiry_date,
        defaults={
            'quantity': total_qty,
            'purchase_rate': latest_item.purchase_rate,
            'mrp': latest_item.mrp,
        }
    )
    if not created:
        stock.quantity = total_qty
        stock.purchase_rate = latest_item.purchase_rate
        stock.mrp = latest_item.mrp
        stock.save()


def _parse_items_from_post(request):
    """Read the parallel item-row arrays submitted by the dynamic purchase form."""
    products = request.POST.getlist('item_product[]')
    batches = request.POST.getlist('item_batch[]')
    expiries = request.POST.getlist('item_expiry[]')
    quantities = request.POST.getlist('item_quantity[]')
    free_quantities = request.POST.getlist('item_free_quantity[]')
    rates = request.POST.getlist('item_purchase_rate[]')
    mrps = request.POST.getlist('item_mrp[]')
    gst_rates = request.POST.getlist('item_gst_rate[]')
    discounts = request.POST.getlist('item_discount_percent[]')

    rows = []
    for i in range(len(products)):
        if not products[i] or not batches[i]:
            continue
        rows.append({
            'product_id': products[i],
            'batch_number': batches[i].strip(),
            'expiry_date': expiries[i],
            'quantity': _to_int(quantities[i] if i < len(quantities) else 0),
            'free_quantity': _to_int(free_quantities[i] if i < len(free_quantities) else 0, 0),
            'purchase_rate': _to_decimal(rates[i] if i < len(rates) else 0),
            'mrp': _to_decimal(mrps[i] if i < len(mrps) else 0),
            'gst_rate': _to_decimal(gst_rates[i] if i < len(gst_rates) else 12),
            'discount_percent': _to_decimal(discounts[i] if i < len(discounts) else 0),
        })
    return rows


# ==================== PURCHASE LIST ====================
# @login_required
def purchase_list(request):
    purchases = PurchaseMaster.objects.filter(is_deleted=False).select_related('supplier').prefetch_related('items')
    context = {
        'purchases': purchases,
        'page_title': 'Purchase Entries'
    }
    return render(request, 'purchases/purchase_list.html', context)


# ==================== PURCHASE CREATE ====================
# @login_required
@transaction.atomic
def purchase_create(request):
    suppliers = SupplierMaster.objects.filter(status=True, is_deleted=False)
    products = ProductMaster.objects.filter(status=True, is_deleted=False)

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        invoice_number = request.POST.get('invoice_number', '').strip()
        invoice_date = request.POST.get('invoice_date')
        remarks = request.POST.get('remarks', '')

        item_rows = _parse_items_from_post(request)

        if not supplier_id or not invoice_number or not invoice_date:
            messages.error(request, 'Supplier, Invoice Number and Invoice Date are required.')
        elif PurchaseMaster.objects.filter(supplier_id=supplier_id, invoice_number__iexact=invoice_number, is_deleted=False).exists():
            messages.error(request, f"Invoice '{invoice_number}' already exists for this supplier.")
        elif not item_rows:
            messages.error(request, 'Please add at least one product line item to the purchase.')
        else:
            purchase = PurchaseMaster.objects.create(
                supplier_id=supplier_id,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                remarks=remarks,
                created_by=request.user if request.user.is_authenticated else None
            )

            total_amount = Decimal('0')
            batch_keys = set()

            for row in item_rows:
                item = PurchaseItem(
                    purchase=purchase,
                    product_id=row['product_id'],
                    batch_number=row['batch_number'],
                    expiry_date=row['expiry_date'],
                    quantity=row['quantity'],
                    free_quantity=row['free_quantity'],
                    purchase_rate=row['purchase_rate'],
                    mrp=row['mrp'],
                    gst_rate=row['gst_rate'],
                    discount_percent=row['discount_percent'],
                )
                item.save()  # amount computed inside save()
                total_amount += item.amount
                batch_keys.add((item.product_id, item.batch_number, item.expiry_date))

            purchase.total_amount = total_amount
            purchase.save(update_fields=['total_amount'])

            # Create / update batchwise stock for every batch touched by this purchase
            for product_id, batch_number, expiry_date in batch_keys:
                sync_batch_stock(product_id, batch_number, expiry_date)

            messages.success(request, f'Purchase entry saved and batchwise stock updated ({len(item_rows)} item(s)).')
            return redirect('purchase_list')

    context = {
        'suppliers': suppliers,
        'products': products,
        'page_title': 'New Purchase Entry',
    }
    return render(request, 'purchases/purchase_form.html', context)


# ==================== PURCHASE EDIT ====================
# @login_required
@transaction.atomic
def purchase_edit(request, pk):
    purchase = get_object_or_404(PurchaseMaster, pk=pk, is_deleted=False)
    suppliers = SupplierMaster.objects.filter(status=True, is_deleted=False)
    products = ProductMaster.objects.filter(status=True, is_deleted=False)

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        invoice_number = request.POST.get('invoice_number', '').strip()
        invoice_date = request.POST.get('invoice_date')
        remarks = request.POST.get('remarks', '')

        item_rows = _parse_items_from_post(request)

        if not supplier_id or not invoice_number or not invoice_date:
            messages.error(request, 'Supplier, Invoice Number and Invoice Date are required.')
        elif PurchaseMaster.objects.filter(supplier_id=supplier_id, invoice_number__iexact=invoice_number, is_deleted=False).exclude(pk=pk).exists():
            messages.error(request, f"Invoice '{invoice_number}' already exists for this supplier.")
        elif not item_rows:
            messages.error(request, 'Please add at least one product line item to the purchase.')
        else:
            # Remember old batch keys before wiping items, so their stock gets recalculated too
            old_batch_keys = set(
                purchase.items.values_list('product_id', 'batch_number', 'expiry_date')
            )

            purchase.supplier_id = supplier_id
            purchase.invoice_number = invoice_number
            purchase.invoice_date = invoice_date
            purchase.remarks = remarks

            # Simplest reliable approach for a dynamic-row formset: replace all line items
            purchase.items.all().delete()

            total_amount = Decimal('0')
            new_batch_keys = set()

            for row in item_rows:
                item = PurchaseItem(
                    purchase=purchase,
                    product_id=row['product_id'],
                    batch_number=row['batch_number'],
                    expiry_date=row['expiry_date'],
                    quantity=row['quantity'],
                    free_quantity=row['free_quantity'],
                    purchase_rate=row['purchase_rate'],
                    mrp=row['mrp'],
                    gst_rate=row['gst_rate'],
                    discount_percent=row['discount_percent'],
                )
                item.save()
                total_amount += item.amount
                new_batch_keys.add((item.product_id, item.batch_number, item.expiry_date))

            purchase.total_amount = total_amount
            purchase.save()

            # Recalculate stock for every batch touched, old or new
            for product_id, batch_number, expiry_date in old_batch_keys | new_batch_keys:
                sync_batch_stock(product_id, batch_number, expiry_date)

            messages.success(request, 'Purchase entry updated and batchwise stock re-synced.')
            return redirect('purchase_list')

    context = {
        'purchase': purchase,
        'items': purchase.items.select_related('product'),
        'suppliers': suppliers,
        'products': products,
        'page_title': 'Edit Purchase Entry',
    }
    return render(request, 'purchases/purchase_form.html', context)


# ==================== PURCHASE DETAIL (VIEW) ====================
# @login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(PurchaseMaster.objects.select_related('supplier'), pk=pk, is_deleted=False)
    items = purchase.items.select_related('product', 'product__company')
    context = {
        'purchase': purchase,
        'items': items,
        'page_title': f'Purchase Invoice - {purchase.invoice_number}',
    }
    return render(request, 'purchases/purchase_detail.html', context)


# ==================== PURCHASE DELETE (SOFT DELETE) ====================
# @login_required
@transaction.atomic
def purchase_delete(request, pk):
    purchase = get_object_or_404(PurchaseMaster, pk=pk)

    batch_keys = set(
        purchase.items.values_list('product_id', 'batch_number', 'expiry_date')
    )

    purchase.is_deleted = True
    purchase.save(update_fields=['is_deleted'])

    # Recalculate stock for every batch this purchase had contributed to,
    # so the deleted purchase's quantity is removed from batchwise stock.
    for product_id, batch_number, expiry_date in batch_keys:
        sync_batch_stock(product_id, batch_number, expiry_date)

    messages.success(request, 'Purchase entry deleted and batchwise stock re-synced.')
    return redirect('purchase_list')


# ==================== BATCHWISE STOCK LIST ====================
# @login_required
def batch_stock_list(request):
    stocks = BatchStock.objects.filter(quantity__gt=0).select_related('product', 'product__company')
    context = {
        'stocks': stocks,
        'page_title': 'Batchwise Stock',
    }
    return render(request, 'purchases/batch_stock_list.html', context)
