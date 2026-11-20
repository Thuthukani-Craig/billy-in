from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import TenantMembership
from .tenant_context import resolve_request_tenant


class TenantWorkspacePermission(BasePermission):
    """Allow reads to members and writes only to operational tenant roles."""

    message = "Your tenant role does not permit this action."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or request.user.is_superuser:
            return True
        try:
            tenant = resolve_request_tenant(request)
        except Exception:
            return False
        return TenantMembership.objects.filter(
            user=request.user,
            tenant=tenant,
            is_active=True,
            role__in=[
                TenantMembership.ROLE_OWNER,
                TenantMembership.ROLE_ADMIN,
                TenantMembership.ROLE_MANAGER,
            ],
        ).exists()
