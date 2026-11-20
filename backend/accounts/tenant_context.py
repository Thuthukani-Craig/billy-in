from rest_framework.exceptions import ValidationError

from .models import TenantMembership


def resolve_request_tenant(request):
    """Resolve one tenant from an authenticated request without guessing.

    A single active membership is unambiguous. Users with multiple memberships
    must send X-Tenant-ID so write operations cannot silently target the wrong
    organisation.
    """
    if request.user.is_superuser:
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            raise ValidationError({"tenant": "Platform administrators must select a tenant for this operation."})
        from .models import Tenant
        try:
            return Tenant.objects.get(pk=tenant_id, is_active=True)
        except (Tenant.DoesNotExist, ValueError):
            raise ValidationError({"tenant": "The selected tenant is unavailable."})

    memberships = TenantMembership.objects.filter(
        user=request.user, is_active=True, tenant__is_active=True
    ).select_related("tenant")

    selected_id = request.headers.get("X-Tenant-ID")
    if selected_id:
        membership = memberships.filter(tenant_id=selected_id).first()
        if membership is None:
            raise ValidationError({"tenant": "You do not have access to the selected tenant."})
        return membership.tenant

    if memberships.count() == 1:
        return memberships.get().tenant
    if not memberships.exists():
        raise ValidationError({"tenant": "Your account is not assigned to an active tenant."})
    raise ValidationError({"tenant": "Select a business workspace before creating records."})
