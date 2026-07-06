from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from wholesaleApp.models.customers import CustomerMaster, AreaMaster

# @login_required
def customer_list(request):
    customers = CustomerMaster.objects.filter(is_deleted=False).select_related('area')
    context = {
        'customers': customers,
        'page_title': 'Customer Master'
    }
    return render(request, 'customers/customer_list.html', context)

# @login_required
def customer_create(request):
    areas = AreaMaster.objects.filter(is_active=True)
    if request.method == 'POST':
        # Form handling (simple version - aap forms.py bana sakte ho baad mein)
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
            created_by=request.user
        )
        customer.save()
        messages.success(request, 'Customer created successfully!')
        return redirect('customer_list')
    
    context = {'areas': areas, 'page_title': 'Add New Customer'}
    return render(request, 'customers/customer_form.html', context)

@login_required
def customer_edit(request, pk):
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
    
    context = {'customer': customer, 'areas': areas, 'page_title': 'Edit Customer'}
    return render(request, 'customers/customer_form.html', context)

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(CustomerMaster, pk=pk)
    customer.is_deleted = True
    customer.save()
    messages.success(request, 'Customer deleted successfully!')
    return redirect('customer_list')