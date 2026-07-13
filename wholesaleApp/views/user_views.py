from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from wholesaleApp.models.permissions import UserProfile
from wholesaleApp.views.security_helpers import get_user_permissions_context

# ==================== USER MANAGEMENT CRUD ====================

def user_list(request):
    """List all employees/users with search & actions."""
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Only Shop Owners can manage users.")
        return redirect('home')

    users = User.objects.filter(is_superuser=False).select_related('profile')
    context = {
        'users': users,
        'page_title': 'User Management (Staff & Field Boys)',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'master/user_list.html', context)


def user_create(request):
    """Create a new employee user & auto profile creation."""
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Only Shop Owners can add users.")
        return redirect('home')

    if request.method == 'POST':
        username = request.POST['username'].strip()
        email = request.POST.get('email', '').strip()
        password = request.POST['password']
        role = request.POST.get('role', 'Employee')
        mobile = request.POST.get('mobile', '').strip()

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, f"User with username '{username}' already exists.")
        else:
            # Create django User
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # Retrieve or create profile (signal might have run, but let's be safe)
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.mobile = mobile
            profile.save()

            messages.success(request, f"Employee user '{username}' successfully created!")
            return redirect('user_list')

    context = {
        'roles': ['Employee', 'Salesman', 'Delivery Boy'],
        'page_title': 'Add New Staff / Field Operator',
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'master/user_form.html', context)


def user_edit(request, pk):
    """Edit existing employee user details."""
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Only Shop Owners can edit users.")
        return redirect('home')

    target_user = get_object_or_404(User, id=pk, is_superuser=False)
    profile, created = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        username = request.POST['username'].strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'Employee')
        mobile = request.POST.get('mobile', '').strip()

        if User.objects.filter(username__iexact=username).exclude(id=pk).exists():
            messages.error(request, f"Username '{username}' is already in use by another user.")
        else:
            target_user.username = username
            target_user.email = email
            target_user.save()

            profile.role = role
            profile.mobile = mobile
            profile.save()

            messages.success(request, f"User '{username}' details updated successfully!")
            return redirect('user_list')

    context = {
        'target_user': target_user,
        'profile': profile,
        'roles': ['Employee', 'Salesman', 'Delivery Boy'],
        'page_title': f"Edit Staff: {target_user.username}",
        'user_perms': get_user_permissions_context(request.user)
    }
    return render(request, 'master/user_form.html', context)


def user_delete(request, pk):
    """Delete an employee user."""
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Only Shop Owners can delete users.")
        return redirect('home')

    target_user = get_object_or_404(User, id=pk, is_superuser=False)
    username = target_user.username
    target_user.delete()

    messages.success(request, f"Employee user '{username}' deleted successfully!")
    return redirect('user_list')
