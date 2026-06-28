from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'manufacturer', 'sale_price', 'stock_quantity']
    list_filter = ['category', 'manufacturer']
    search_fields = ['name', 'sku', 'manufacturer']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'category', 'manufacturer')
        }),
        ('Batch Information', {
            'fields': ('batch_number', 'expiry_date')
        }),
        ('Pricing', {
            'fields': ('purchase_price', 'sale_price')
        }),
        ('Stock Management', {
            'fields': ('stock_quantity', 'min_stock_level')
        }),
    )

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['pharmacy_name', 'name', 'phone', 'email']
    search_fields = ['pharmacy_name', 'name', 'phone']
    fieldsets = (
        ('Pharmacy Information', {
            'fields': ('pharmacy_name', 'name')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address')
        }),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'order_date', 'total_amount', 'status']
    list_filter = ['status', 'order_date']
    search_fields = ['customer__pharmacy_name', 'id']
    readonly_fields = ['order_date', 'total_amount']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'subtotal']
    search_fields = ['order__id', 'product__name']
    readonly_fields = ['subtotal']
