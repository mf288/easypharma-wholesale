from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db.models import Sum, Count, Q

from .models import Category, Product, Customer, Order, OrderItem



def dashboard(request):
    pass



# Product Views
def product_list(request):
    """List all products with search and filter"""
    products = Product.objects.all()
    categories = Category.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(sku__icontains=search_query) |
            Q(manufacturer__icontains=search_query)
        )
    
    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
    }
    return render(request, 'products/list.html', context)

def product_detail(request, pk):
    """View product details"""
    product = get_object_or_404(Product, pk=pk)
    context = {'product': product}
    return render(request, 'products/detail.html', context)

def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        category_id = request.POST.get('category')
        product = Product.objects.create(
            name=request.POST.get('name'),
            sku=request.POST.get('sku'),
            category_id=category_id,
            manufacturer=request.POST.get('manufacturer'),
            batch_number=request.POST.get('batch_number'),
            expiry_date=request.POST.get('expiry_date'),
            purchase_price=request.POST.get('purchase_price'),
            sale_price=request.POST.get('sale_price'),
            stock_quantity=request.POST.get('stock_quantity'),
            min_stock_level=request.POST.get('min_stock_level', 10),
        )
        return redirect('product_detail', pk=product.pk)
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'products/form.html', context)

def product_edit(request, pk):
    """Edit existing product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.sku = request.POST.get('sku')
        product.category_id = request.POST.get('category')
        product.manufacturer = request.POST.get('manufacturer')
        product.batch_number = request.POST.get('batch_number')
        product.expiry_date = request.POST.get('expiry_date')
        product.purchase_price = request.POST.get('purchase_price')
        product.sale_price = request.POST.get('sale_price')
        product.stock_quantity = request.POST.get('stock_quantity')
        product.min_stock_level = request.POST.get('min_stock_level')
        product.save()
        return redirect('product_detail', pk=product.pk)
    
    categories = Category.objects.all()
    context = {'product': product, 'categories': categories}
    return render(request, 'products/form.html', context)

def product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/confirm_delete.html', {'product': product})

# Customer Views
def customer_list(request):
    """List all customers"""
    customers = Customer.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(pharmacy_name__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    context = {
        'customers': customers,
        'search_query': search_query,
    }
    return render(request, 'customers/list.html', context)

def customer_detail(request, pk):
    """View customer details and their orders"""
    customer = get_object_or_404(Customer, pk=pk)
    orders = Order.objects.filter(customer=customer).order_by('-order_date')
    
    context = {
        'customer': customer,
        'orders': orders,
    }
    return render(request, 'customers/detail.html', context)

def customer_create(request):
    """Create new customer"""
    if request.method == 'POST':
        customer = Customer.objects.create(
            name=request.POST.get('name'),
            pharmacy_name=request.POST.get('pharmacy_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
        )
        return redirect('customer_detail', pk=customer.pk)
    
    return render(request, 'customers/form.html')

def customer_edit(request, pk):
    """Edit existing customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.pharmacy_name = request.POST.get('pharmacy_name')
        customer.phone = request.POST.get('phone')
        customer.email = request.POST.get('email')
        customer.address = request.POST.get('address')
        customer.save()
        return redirect('customer_detail', pk=customer.pk)
    
    context = {'customer': customer}
    return render(request, 'customers/form.html', context)

def customer_delete(request, pk):
    """Delete customer"""
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')
    return render(request, 'customers/confirm_delete.html', {'customer': customer})

# Order Views
def order_list(request):
    """List all orders"""
    orders = Order.objects.all().order_by('-order_date')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    
    context = {
        'orders': orders,
        'selected_status': status,
    }
    return render(request, 'orders/list.html', context)

def order_detail(request, pk):
    """View order details"""
    order = get_object_or_404(Order, pk=pk)
    items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'orders/detail.html', context)

def order_create(request):
    """Create new order"""
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer = get_object_or_404(Customer, pk=customer_id)
        
        order = Order.objects.create(
            customer=customer,
            total_amount=0,
            status='Pending'
        )
        
        # Add items to order
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        
        total = 0
        for product_id, quantity in zip(product_ids, quantities):
            if product_id and quantity:
                product = get_object_or_404(Product, pk=product_id)
                qty = int(quantity)
                subtotal = product.sale_price * qty
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    unit_price=product.sale_price,
                    subtotal=subtotal
                )
                
                # Update stock
                product.stock_quantity -= qty
                product.save()
                
                total += subtotal
        
        order.total_amount = total
        order.save()
        
        return redirect('order_detail', pk=order.pk)
    
    customers = Customer.objects.all()
    products = Product.objects.filter(stock_quantity__gt=0)
    
    context = {
        'customers': customers,
        'products': products,
    }
    return render(request, 'orders/form.html', context)

def order_edit_status(request, pk):
    """Update order status"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Completed', 'Cancelled']:
            order.status = new_status
            order.save()
        return redirect('order_detail', pk=order.pk)
    
    context = {'order': order}
    return render(request, 'orders/edit_status.html', context)

# Category Views
def category_list(request):
    """List all categories"""
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'categories/list.html', context)

def category_create(request):
    """Create new category"""
    if request.method == 'POST':
        Category.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('category_list')
    
    return render(request, 'categories/form.html')

# Reports/Analytics Views
def reports(request):
    """Generate reports and analytics"""
    # Sales by category
    sales_by_category = OrderItem.objects.values('product__category__name').annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum('subtotal')
    )
    
    # Top selling products
    top_products = OrderItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum('subtotal')
    ).order_by('-total_sales')[:10]
    
    # Monthly sales
    today = datetime.now()
    last_30_days = today - timedelta(days=30)
    monthly_sales = Order.objects.filter(
        order_date__gte=last_30_days,
        status='Completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'sales_by_category': sales_by_category,
        'top_products': top_products,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'reports.html', context)

# API endpoints for AJAX
def api_get_products(request):
    """API endpoint to get products as JSON"""
    products = Product.objects.values('id', 'name', 'sku', 'sale_price', 'stock_quantity')
    return JsonResponse(list(products), safe=False)

def api_get_customers(request):
    """API endpoint to get customers as JSON"""
    customers = Customer.objects.values('id', 'pharmacy_name', 'phone', 'email')
    return JsonResponse(list(customers), safe=False)
