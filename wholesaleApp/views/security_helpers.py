from django.contrib.auth.models import User
from wholesaleApp.models.permissions import AppGroupModule, AppFeature, UserFeaturePermission
from wholesaleApp.models.tenant import Tenant

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

def seed_default_tenant():
    """Ensure at least one default tenant exists."""
    default_tenant, created = Tenant.objects.get_or_create(
        name="Default Tenant",
        defaults={
            "company_name": "EasyPharma Wholesale Default",
            "address": "123 Main Street, Central City",
            "phone": "9876543210",
            "email": "info@easypharma.com",
            "gstin": "27AAPCG1234F1Z5",
            "dl_number": "DL-12345/20A/21B"
        }
    )
    return default_tenant

def seed_default_permissions():
    """Seed the database with default Modules and Features if they don't exist."""
    # First ensure default tenant exists
    default_tenant = seed_default_tenant()

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

    # Ensure UserProfile exists for all users and has a tenant
    from wholesaleApp.models.permissions import UserProfile
    for user in User.objects.all():
        profile, created = UserProfile.objects.get_or_create(user=user)
        if not profile.tenant:
            profile.tenant = default_tenant
        if user.is_superuser and profile.role != 'Owner':
            profile.role = 'Owner'
        profile.save()

    # Assign all legacy/existing business objects without a tenant to the default tenant
    from wholesaleApp.models.customers import AreaMaster, SubareaMaster, CustomerMaster
    from wholesaleApp.models.supplier import SupplierMaster
    from wholesaleApp.models.products import CompanyMaster, DrugMaster, ProductTypeMaster, ProductMaster
    from wholesaleApp.models.purchase import ProductBatch, PurchaseOrder, PurchaseOrderItem, PurchaseEntry, PurchaseEntryItem
    from wholesaleApp.models.sales import SalesInvoice, SalesInvoiceItem

    models_to_update = [
        AreaMaster, SubareaMaster, CustomerMaster, SupplierMaster,
        CompanyMaster, DrugMaster, ProductTypeMaster, ProductMaster,
        ProductBatch, PurchaseOrder, PurchaseOrderItem, PurchaseEntry,
        PurchaseEntryItem, SalesInvoice, SalesInvoiceItem
    ]
    for model in models_to_update:
        if hasattr(model, 'unfiltered_objects'):
            model.unfiltered_objects.filter(tenant__isnull=True).update(tenant=default_tenant)

    # For superusers/owners, auto-grant all permissions
    all_features = AppFeature.objects.all()
    for user in User.objects.filter(is_superuser=True):
        for f in all_features:
            UserFeaturePermission.objects.get_or_create(
                user=user,
                feature=f,
                defaults={'is_granted': True}
            )


def user_perms_context_processor(request):
    """Context processor to make user_perms set globally available in all templates."""
    return {
        'user_perms': get_user_permissions_context(request.user)
    }

def tenant_context_processor(request):
    """Context processor to make tenant info globally available in templates."""
    context = {
        'current_tenant': getattr(request, 'tenant', None),
        'tenants_list': [],
    }
    if request.user.is_authenticated and request.user.is_superuser:
        context['tenants_list'] = Tenant.objects.filter(is_active=True)
    return context
