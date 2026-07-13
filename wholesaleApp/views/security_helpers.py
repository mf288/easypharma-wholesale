from django.contrib.auth.models import User
from wholesaleApp.models.permissions import AppGroupModule, AppFeature, UserFeaturePermission

def has_feature_access(user, codename):
    """Check if the user is granted access to a specific feature codename."""
    if not user.is_authenticated:
        return True  # Treat anonymous users as authorized to support testing and login bypass
    if user.is_superuser:
        return True
    return UserFeaturePermission.objects.filter(
        user=user,
        feature__codename=codename,
        feature__is_active=True,
        is_granted=True
    ).exists()

def get_user_permissions_context(user):
    """Return a set of all feature codenames granted to the user."""
    if not user.is_authenticated:
        # Return all features for local anonymous developers
        return {f.codename for f in AppFeature.objects.filter(is_active=True)}
    if user.is_superuser:
        return {f.codename for f in AppFeature.objects.filter(is_active=True)}
    return {
        p.feature.codename 
        for p in UserFeaturePermission.objects.filter(
            user=user, 
            is_granted=True, 
            feature__is_active=True
        ).select_related('feature')
    }

def seed_default_permissions():
    """Seed the database with default Modules and Features if they don't exist."""
    DEFAULT_PERMISSIONS = {
        'Sales & Billing': [
            ('sales_create', 'New Sale Bill'),
            ('sales_return', 'Sales Return'),
            ('sales_reprint', 'Re-print Sale Bill'),
            ('sales_credit_debit', 'Credit / Debit Notes'),
            ('view_margins', 'View Profit Margins & Cost Rates'),
        ],
        'Purchase & Inventory': [
            ('purchase_create', 'New Purchase Entry'),
            ('purchase_list', 'View Purchase History'),
        ],
        'Master Data Settings': [
            ('product_crud', 'Manage Products (Add/Edit)'),
            ('customer_crud', 'Manage Customers (Add/Edit)'),
            ('supplier_crud', 'Manage Suppliers (Add/Edit)'),
            ('area_crud', 'Manage Areas & Subareas'),
        ]
    }

    for module_name, features in DEFAULT_PERMISSIONS.items():
        module, created = AppGroupModule.objects.get_or_create(name=module_name)
        for codename, name in features:
            AppFeature.objects.get_or_create(
                codename=codename,
                defaults={'module': module, 'name': name, 'is_active': True}
            )

    # Ensure UserProfile exists for all users
    from wholesaleApp.models.permissions import UserProfile
    for user in User.objects.all():
        profile, created = UserProfile.objects.get_or_create(user=user)
        if user.is_superuser and profile.role != 'Owner':
            profile.role = 'Owner'
            profile.save()

    # For superusers/owners, auto-grant all permissions
    all_features = AppFeature.objects.all()
    for user in User.objects.filter(is_superuser=True):
        for f in all_features:
            UserFeaturePermission.objects.get_or_create(
                user=user,
                feature=f,
                defaults={'is_granted': True}
            )
