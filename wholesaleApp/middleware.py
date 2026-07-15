import threading
from django.utils.deprecation import MiddlewareMixin
from wholesaleApp.models.tenant import Tenant, set_current_tenant

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tenant = None
        if request.user.is_authenticated:
            # Check session for an active tenant ID
            session_tenant_id = request.session.get('active_tenant_id')
            if session_tenant_id:
                try:
                    tenant = Tenant.objects.get(id=session_tenant_id, is_active=True)
                except Tenant.DoesNotExist:
                    pass
            
            # If no active tenant in session, look up user profile's tenant
            if not tenant and hasattr(request.user, 'profile') and request.user.profile.tenant:
                tenant = request.user.profile.tenant
                request.session['active_tenant_id'] = tenant.id
        
        # Set the thread-local tenant
        set_current_tenant(tenant)
        request.tenant = tenant

    def process_response(self, request, response):
        # Clear thread-local tenant to prevent memory leaks / context bleeding
        set_current_tenant(None)
        return response
