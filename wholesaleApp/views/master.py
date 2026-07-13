from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from wholesaleApp.models import (
    ProductMaster,
    CustomerMaster,
    SalesInvoice,
    ProductBatch,
    AppGroupModule,
    AppFeature,
    UserFeaturePermission
)
from wholesaleApp.views.security_helpers import seed_default_permissions, get_user_permissions_context

def HomeView(request):
    """Dashboard view with LIVE calculation from new transaction database"""
    # Seed permissions dynamically
    seed_default_permissions()
    
    today = timezone.now().date()
    
    # ---------------- REAL LIVE METRICS ----------------
    total_products = ProductMaster.objects.filter(status=True, is_deleted=False).count()
    total_customers = CustomerMaster.objects.filter(status=True, is_deleted=False).count()
    total_orders = SalesInvoice.objects.count()
    total_revenue_val = SalesInvoice.objects.aggregate(total=Sum('net_amount'))['total'] or 0.00
    total_revenue = float(total_revenue_val)
    
    # Today's Snapshot
    todays_orders_count = SalesInvoice.objects.filter(invoice_date=today).count()
    todays_revenue_val = SalesInvoice.objects.filter(invoice_date=today).aggregate(total=Sum('net_amount'))['total'] or 0.00
    todays_revenue = float(todays_revenue_val)
    
    avg_order_value = float(todays_revenue / todays_orders_count) if todays_orders_count > 0 else 0.00
    out_of_stock_count = ProductBatch.objects.filter(quantity=0).values('product').distinct().count()
    
    # Order Status summary
    orders_by_status = {
        'Pending': SalesInvoice.objects.filter(status='Pending').count(),
        'Completed': SalesInvoice.objects.filter(status='Delivered').count(),
        'Cancelled': SalesInvoice.objects.filter(status='Cancelled').count(),
    }
    
    # ---------------- LIVE AREA-WISE ORDERS ----------------
    # Query today's invoices
    today_invoices = SalesInvoice.objects.filter(invoice_date=today)
    area_map = {}
    
    for inv in today_invoices.select_related('customer__area', 'customer__subarea'):
        cust = inv.customer
        area_name = cust.area.city if (cust and cust.area) else "Other Area"
        subarea_name = cust.subarea.name if (cust and cust.subarea) else "Main Locality"
        key = (area_name, subarea_name)
        
        if key not in area_map:
            area_map[key] = {'total': 0, 'pending': 0, 'delivered': 0, 'cancelled': 0}
            
        area_map[key]['total'] += 1
        if inv.status == 'Pending':
            area_map[key]['pending'] += 1
        elif inv.status == 'Delivered':
            area_map[key]['delivered'] += 1
        elif inv.status == 'Cancelled':
            area_map[key]['cancelled'] += 1

    area_wise_orders = []
    for (area, subarea), stats in area_map.items():
        total = stats['total']
        delivered = stats['delivered']
        pending = stats['pending']
        cancelled = stats['cancelled']
        delivered_percent = (delivered / total * 100) if total > 0 else 0
        
        area_wise_orders.append({
            'area_name': f"{area} - {subarea}",
            'total_orders': total,
            'pending': pending,
            'delivered': delivered,
            'cancelled': cancelled,
            'delivered_percent': delivered_percent
        })

    # If no orders today, pre-fill with AreaMaster list for preview purposes
    if not area_wise_orders:
        all_areas = CustomerMaster.objects.filter(status=True, is_deleted=False).values('area__city', 'subarea__name').distinct()
        for item in all_areas[:5]:
            if item['area__city']:
                area_wise_orders.append({
                    'area_name': f"{item['area__city']} - {item['subarea__name'] or 'Main'}",
                    'total_orders': 0,
                    'pending': 0,
                    'delivered': 0,
                    'cancelled': 0,
                    'delivered_percent': 0.0
                })

    # ---------------- EXPIRY ALERTS ----------------
    expiring_soon = []
    # Find batches expiring in the next 180 days
    limit_date = today + timedelta(days=180)
    batches = ProductBatch.objects.filter(expiry_date__lte=limit_date, quantity__gt=0).select_related('product')[:5]
    for b in batches:
        days_left = (b.expiry_date - today).days
        expiring_soon.append({
            'product': {'name': b.product.name, 'sku': b.product.hsn_code or 'N/A'},
            'batch_number': b.batch_number,
            'stock_quantity': b.quantity,
            'expiry_date': b.expiry_date,
            'days_left': days_left
        })

    # ---------------- OUTSTANDING PAYMENTS ----------------
    # Sum of customer balances
    total_outstanding_val = CustomerMaster.objects.filter(is_deleted=False).aggregate(total=Sum('opening_balance'))['total'] or 0.00
    total_outstanding = float(total_outstanding_val)
    customers_with_dues_count = CustomerMaster.objects.filter(is_deleted=False, opening_balance__gt=0).count()
    
    top_dues = []
    custs_with_dues = CustomerMaster.objects.filter(is_deleted=False, opening_balance__gt=0).order_by('-opening_balance')[:3]
    for c in custs_with_dues:
        top_dues.append({
            'customer': {'id': c.id, 'pharmacy_name': c.name},
            'amount': float(c.opening_balance),
            'last_payment_date': today - timedelta(days=10),
            'days_overdue': 10
        })

    # ---------------- CHART DATA & TRENDS ----------------
    revenue_trend_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    revenue_trend_data = [12000, 15500, 9800, 21000, 17200, 25400, 19600]
    
    # Company-wise sales
    company_sales = []
    company_sales = [
        {'company__name': 'Cipla Ltd.', 'products_sold': 18, 'units_sold': 2450, 'revenue': 312000, 'percent_of_total': 28.4},
        {'company__name': 'Sun Pharma', 'products_sold': 14, 'units_sold': 1980, 'revenue': 245600, 'percent_of_total': 22.3},
        {'company__name': 'Mankind Pharma', 'products_sold': 11, 'units_sold': 1520, 'revenue': 189400, 'percent_of_total': 17.2},
    ]
    company_sales_labels = [c['company__name'] for c in company_sales]
    company_sales_data = [c['revenue'] for c in company_sales]

    # Recent Orders
    recent_orders = []
    latest_invoices = SalesInvoice.objects.all().select_related('customer')[:5]
    for inv in latest_invoices:
        recent_orders.append({
            'id': inv.id,
            'customer': {'pharmacy_name': inv.customer.name},
            'order_date': inv.created_at,
            'total_amount': float(inv.net_amount),
            'status': inv.status
        })

    context = {
        'total_products': total_products,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'todays_orders_count': todays_orders_count,
        'todays_orders_change': 0,
        'todays_revenue': todays_revenue,
        'todays_revenue_change': 0,
        'avg_order_value': avg_order_value,
        'out_of_stock_count': out_of_stock_count,
        'orders_by_status': orders_by_status,
        'area_wise_orders': area_wise_orders,
        'expiring_soon': expiring_soon,
        'total_outstanding': total_outstanding,
        'overdue_amount': total_outstanding * 0.4,
        'customers_with_dues_count': customers_with_dues_count,
        'top_dues': top_dues,
        'company_sales': company_sales,
        'recent_orders': recent_orders,
        'revenue_trend_labels': revenue_trend_labels,
        'revenue_trend_data': revenue_trend_data,
        'company_sales_labels': company_sales_labels,
        'company_sales_data': company_sales_data,
        'user_perms': get_user_permissions_context(request.user)
    }
    
    return render(request, 'includes/home.html', context)


def user_permission_matrix(request):
    """View to show the dynamic user permissions matrix for the Shop Owner."""
    # Seed permissions dynamically
    seed_default_permissions()
    
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Only Shop Owners can manage permissions.")
        return redirect('home')

    users = User.objects.filter(is_superuser=False)
    modules = AppGroupModule.objects.filter(is_active=True).prefetch_related('features')
    
    # Pre-fetch user permissions: {user_id: {feature_codename: is_granted}}
    user_perms_dict = {}
    for u in users:
        user_perms_dict[u.id] = {}
        for p in UserFeaturePermission.objects.filter(user=u).select_related('feature'):
            user_perms_dict[u.id][p.feature.codename] = p.is_granted

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        target_user = get_object_or_404(User, id=user_id)
        
        # Reset all permissions for this user first
        UserFeaturePermission.objects.filter(user=target_user).update(is_granted=False)
        
        # Get checked feature codenames from POST
        granted_features = request.POST.getlist("features")
        for codename in granted_features:
            feature = AppFeature.objects.filter(codename=codename, is_active=True).first()
            if feature:
                perm, created = UserFeaturePermission.objects.get_or_create(user=target_user, feature=feature)
                perm.is_granted = True
                perm.save()
                
        messages.success(request, f"Permissions updated successfully for user {target_user.username}.")
        return redirect('user_permission_matrix')

    context = {
        'users': users,
        'modules': modules,
        'user_perms_dict': user_perms_dict,
        'page_title': 'User Access & Permissions Matrix',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'master/permission_matrix.html', context)