from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from wholesaleApp.models.customers import CustomerMaster, AreaMaster, SubareaMaster

# ==================== CUSTOMER MASTER VIEWS ====================
# @login_required
def customer_list(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'customer_crud'):
        messages.error(request, "Access Denied: You do not have permission to view Customers.")
        return redirect('home')
        
    customers = CustomerMaster.objects.filter(is_deleted=False).select_related('area')
    context = {
        'customers': customers,
        'page_title': 'Customer Master',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/customer_list.html', context)

# @login_required
def customer_create(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'customer_crud'):
        messages.error(request, "Access Denied: You do not have permission to create Customers.")
        return redirect('home')
        
    areas = AreaMaster.objects.filter(is_active=True)
    if request.method == 'POST':
        # Form handling (simple version)
        customer = CustomerMaster(
            name=request.POST['name'],
            mobile=request.POST['mobile'],
            area_id=request.POST['area'],
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            pincode=request.POST.get('pincode', ''),
            opening_balance=request.POST.get('opening_balance', 0),
            credit_limit=request.POST.get('credit_limit', 0),
            credit_days=request.POST.get('credit_days', 0),
            created_by=request.user if request.user.is_authenticated else None
        )
        customer.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('json') == 'true':
            return JsonResponse({
                'status': 'success',
                'id': customer.id,
                'name': customer.name,
                'city': customer.city
            })
            
        messages.success(request, 'Customer created successfully!')
        return redirect('customer_list')
    
    context = {
        'areas': areas, 
        'page_title': 'Add New Customer',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/customer_form.html', context)

# @login_required
def customer_edit(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'customer_crud'):
        messages.error(request, "Access Denied: You do not have permission to edit Customers.")
        return redirect('home')
        
    customer = get_object_or_404(CustomerMaster, pk=pk, is_deleted=False)
    areas = AreaMaster.objects.filter(is_active=True)
    
    if request.method == 'POST':
        customer.name = request.POST['name']
        customer.mobile = request.POST['mobile']
        customer.area_id = request.POST['area']
        customer.address = request.POST.get('address', '')
        customer.city = request.POST.get('city', '')
        customer.state = request.POST.get('state', '')
        customer.pincode = request.POST.get('pincode', '')
        customer.opening_balance = request.POST.get('opening_balance', 0)
        customer.credit_limit = request.POST.get('credit_limit', 0)
        customer.credit_days = request.POST.get('credit_days', 0)
        customer.save()
        messages.success(request, 'Customer updated successfully!')
        return redirect('customer_list')
    
    context = {
        'customer': customer, 
        'areas': areas, 
        'page_title': 'Edit Customer',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/customer_form.html', context)

# @login_required
def customer_delete(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access
    if not has_feature_access(request.user, 'customer_crud'):
        messages.error(request, "Access Denied: You do not have permission to delete Customers.")
        return redirect('home')
        
    customer = get_object_or_404(CustomerMaster, pk=pk)
    customer.is_deleted = True
    customer.save()
    messages.success(request, 'Customer deleted successfully!')
    return redirect('customer_list')


# ==================== AREA MASTER VIEWS ====================
# @login_required
def area_list(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'area_crud'):
        messages.error(request, "Access Denied: You do not have permission to view Areas.")
        return redirect('home')
        
    areas = AreaMaster.objects.filter(is_active=True)
    subareas = SubareaMaster.objects.filter(is_active=True).select_related('area')
    context = {
        'areas': areas,
        'subareas': subareas,
        'page_title': 'Area & Subarea Master',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/area_list.html', context)

# @login_required
def area_create(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'area_crud'):
        messages.error(request, "Access Denied: You do not have permission to create Areas.")
        return redirect('home')
        
    if request.method == 'POST':
        city = request.POST['city']
        code = request.POST.get('code', '')
        
        # Check if already exists
        if AreaMaster.objects.filter(city__iexact=city).exists():
            messages.error(request, f"Area for city '{city}' already exists.")
        else:
            area = AreaMaster(city=city, code=code)
            area.save()
            messages.success(request, 'Area created successfully!')
            return redirect('area_list')
            
    context = {
        'page_title': 'Add New Area',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/area_form.html', context)

# @login_required
def area_edit(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'area_crud'):
        messages.error(request, "Access Denied: You do not have permission to edit Areas.")
        return redirect('home')
        
    area = get_object_or_404(AreaMaster, pk=pk)
    if request.method == 'POST':
        area.city = request.POST['city']
        area.code = request.POST.get('code', '')
        area.save()
        messages.success(request, 'Area updated successfully!')
        return redirect('area_list')
        
    context = {
        'area': area, 
        'page_title': 'Edit Area',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/area_form.html', context)

# @login_required
def area_delete(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access
    if not has_feature_access(request.user, 'area_crud'):
        messages.error(request, "Access Denied: You do not have permission to delete Areas.")
        return redirect('home')
        
    area = get_object_or_404(AreaMaster, pk=pk)
    area.is_active = False
    area.save()
    messages.success(request, 'Area deleted successfully!')
    return redirect('area_list')


# ==================== SUBAREA MASTER VIEWS ====================
# @login_required
def subarea_create(request):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'area_crud'):
        messages.error(request, "Access Denied: You do not have permission to create Subareas.")
        return redirect('home')
        
    areas = AreaMaster.objects.filter(is_active=True)
    if request.method == 'POST':
        area_id = request.POST['area']
        name = request.POST['name']
        
        if SubareaMaster.objects.filter(area_id=area_id, name__iexact=name).exists():
            messages.error(request, f"Subarea '{name}' already exists in this area.")
        else:
            subarea = SubareaMaster(area_id=area_id, name=name)
            subarea.save()
            messages.success(request, 'Subarea created successfully!')
            return redirect('area_list')
            
    context = {
        'areas': areas, 
        'page_title': 'Add New Subarea',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/subarea_form.html', context)

# @login_required
def subarea_edit(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access, get_user_permissions_context
    if not has_feature_access(request.user, 'area_crud'):
        messages.error(request, "Access Denied: You do not have permission to edit Subareas.")
        return redirect('home')
        
    subarea = get_object_or_404(SubareaMaster, pk=pk)
    areas = AreaMaster.objects.filter(is_active=True)
    if request.method == 'POST':
        subarea.area_id = request.POST['area']
        subarea.name = request.POST['name']
        subarea.save()
        messages.success(request, 'Subarea updated successfully!')
        return redirect('area_list')
        
    context = {
        'subarea': subarea, 
        'areas': areas, 
        'page_title': 'Edit Subarea',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'customers/subarea_form.html', context)

# @login_required
def subarea_delete(request, pk):
    from wholesaleApp.views.security_helpers import has_feature_access
    if not has_feature_access(request.user, 'area_crud'):
        messages.error(request, "Access Denied: You do not have permission to delete Subareas.")
        return redirect('home')
        
    subarea = get_object_or_404(SubareaMaster, pk=pk)
    subarea.is_active = False
    subarea.save()
    messages.success(request, 'Subarea deleted successfully!')
    return redirect('area_list')