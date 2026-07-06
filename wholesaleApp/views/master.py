from django.shortcuts import render
from django.views import View
from datetime import datetime, timedelta


def HomeView(request):
    """Dashboard view with DUMMY/MOCK data for preview purposes"""
    
    today = datetime.now()
 
    context = {
        # ---------------- KEY METRICS ----------------
        'total_products': 248,
        'total_customers': 87,
        'total_orders': 512,
        'total_revenue': 1284500,
 
        # ---------------- TODAY'S SNAPSHOT ----------------
        'todays_orders_count': 14,
        'todays_orders_change': 12,
        'todays_revenue': 38250,
        'todays_revenue_change': -4,
        'avg_order_value': 2508,
        'out_of_stock_count': 6,
 
        # ---------------- ORDER STATUS ----------------
        'orders_by_status': {
            'Pending': 23,
            'Completed': 468,
            'Cancelled': 21,
        },

        # ---------------- AREA-WISE ORDERS (core feature) ----------------
        'area_wise_orders': [
            {'area_name': 'Andheri', 'total_orders': 20, 'pending': 5, 'delivered': 15, 'cancelled': 0, 'delivered_percent': 75.0},
            {'area_name': 'Borivali', 'total_orders': 34, 'pending': 8, 'delivered': 24, 'cancelled': 2, 'delivered_percent': 70.6},
            {'area_name': 'Dadar', 'total_orders': 27, 'pending': 3, 'delivered': 22, 'cancelled': 2, 'delivered_percent': 81.5},
            {'area_name': 'Thane', 'total_orders': 18, 'pending': 6, 'delivered': 11, 'cancelled': 1, 'delivered_percent': 61.1},
            {'area_name': 'Vashi', 'total_orders': 12, 'pending': 2, 'delivered': 9, 'cancelled': 1, 'delivered_percent': 75.0},
        ],
        # ---------------- EXPIRY ALERTS ----------------
        'expiring_soon': [
            {
                'product': {'name': 'Paracetamol 500mg', 'sku': 'PCM-500-10S'},
                'batch_number': 'B2024081',
                'stock_quantity': 320,
                'expiry_date': today + timedelta(days=18),
                'days_left': 18,
            },
            {
                'product': {'name': 'Amoxicillin 250mg', 'sku': 'AMX-250-10S'},
                'batch_number': 'B2024077',
                'stock_quantity': 145,
                'expiry_date': today + timedelta(days=42),
                'days_left': 42,
            },
            {
                'product': {'name': 'Cough Syrup 100ml', 'sku': 'CFS-100ML'},
                'batch_number': 'B2024090',
                'stock_quantity': 60,
                'expiry_date': today + timedelta(days=75),
                'days_left': 75,
            },
        ],
 
        # ---------------- OUTSTANDING PAYMENTS ----------------
        'total_outstanding': 186400,
        'overdue_amount': 92300,
        'customers_with_dues_count': 11,
        'top_dues': [
            {
                'customer': {'id': 1, 'pharmacy_name': 'Shree Ganesh Medical Store'},
                'amount': 42500,
                'last_payment_date': today - timedelta(days=48),
                'days_overdue': 48,
            },
            {
                'customer': {'id': 2, 'pharmacy_name': 'City Care Pharmacy'},
                'amount': 28750,
                'last_payment_date': today - timedelta(days=35),
                'days_overdue': 35,
            },
            {
                'customer': {'id': 3, 'pharmacy_name': 'Apollo Wellness Chemist'},
                'amount': 19600,
                'last_payment_date': today - timedelta(days=12),
                'days_overdue': 12,
            },
        ],
 
        # ---------------- COMPANY-WISE SALES ----------------
        'company_sales': [
            {'company__name': 'Cipla Ltd.', 'products_sold': 18, 'units_sold': 2450, 'revenue': 312000, 'percent_of_total': 28.4},
            {'company__name': 'Sun Pharma', 'products_sold': 14, 'units_sold': 1980, 'revenue': 245600, 'percent_of_total': 22.3},
            {'company__name': 'Mankind Pharma', 'products_sold': 11, 'units_sold': 1520, 'revenue': 189400, 'percent_of_total': 17.2},
            {'company__name': 'Dr. Reddy\'s Labs', 'products_sold': 9, 'units_sold': 1105, 'revenue': 142800, 'percent_of_total': 13.0},
            {'company__name': 'Zydus Healthcare', 'products_sold': 7, 'units_sold': 890, 'revenue': 98500, 'percent_of_total': 9.0},
        ],
 
        # ---------------- TOP CUSTOMERS ----------------
        'top_customers': [
            {'customer__pharmacy_name': 'Shree Ganesh Medical Store', 'order_count': 34, 'total_business': 186500},
            {'customer__pharmacy_name': 'City Care Pharmacy', 'order_count': 28, 'total_business': 152300},
            {'customer__pharmacy_name': 'Apollo Wellness Chemist', 'order_count': 21, 'total_business': 98400},
        ],
 
        # ---------------- RECENT ORDERS ----------------
        'recent_orders': [
            {'id': 1042, 'customer': {'pharmacy_name': 'Shree Ganesh Medical Store'}, 'order_date': today - timedelta(hours=2), 'total_amount': 5480, 'status': 'Pending'},
            {'id': 1041, 'customer': {'pharmacy_name': 'City Care Pharmacy'}, 'order_date': today - timedelta(hours=5), 'total_amount': 3220, 'status': 'Completed'},
            {'id': 1040, 'customer': {'pharmacy_name': 'Apollo Wellness Chemist'}, 'order_date': today - timedelta(hours=9), 'total_amount': 1875, 'status': 'Completed'},
            {'id': 1039, 'customer': {'pharmacy_name': 'Wellcare Pharma'}, 'order_date': today - timedelta(days=1), 'total_amount': 6720, 'status': 'Cancelled'},
            {'id': 1038, 'customer': {'pharmacy_name': 'MedPlus Distributors'}, 'order_date': today - timedelta(days=1, hours=3), 'total_amount': 2990, 'status': 'Completed'},
        ],
 
        # ---------------- LOW STOCK PRODUCTS ----------------
        'low_stock': [
            {'name': 'Insulin Injection 10ml', 'sku': 'INS-10ML', 'stock_quantity': 4, 'min_stock_level': 20, 'category': {'name': 'Diabetes Care'}},
            {'name': 'Surgical Gloves (Box)', 'sku': 'GLV-BOX-100', 'stock_quantity': 7, 'min_stock_level': 25, 'category': {'name': 'Surgical'}},
            {'name': 'Antiseptic Solution 500ml', 'sku': 'ANT-500ML', 'stock_quantity': 9, 'min_stock_level': 15, 'category': {'name': 'General'}},
        ],
 
        # ---------------- CHART DATA (required for graphs) ----------------
        'revenue_trend_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'revenue_trend_data': [12000, 15500, 9800, 21000, 17200, 25400, 19600],
        'company_sales_labels': ['Cipla Ltd.', 'Sun Pharma', 'Mankind Pharma', "Dr. Reddy's Labs", 'Zydus Healthcare'],
        'company_sales_data': [312000, 245600, 189400, 142800, 98500],
    }
    return render(request, 'includes/home.html', context)