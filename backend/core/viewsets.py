from rest_framework import mixins, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated


class HasTenant(BasePermission):
    def has_permission(self, request, view):
        return request.user.tenant_id is not None


class TenantScopedViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Subclass this and set `queryset` + `serializer_class`. Isolation comes free."""

    permission_classes = [IsAuthenticated, HasTenant]

    def get_queryset(self):
        return super().get_queryset().filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
