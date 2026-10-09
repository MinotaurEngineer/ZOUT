from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .metrics import repeat_guest_rate
from .models import MenuItem, Order, WebhookEvent
from .serializers import MenuItemSerializer, OrderSerializer
from .viewsets import HasTenant, TenantScopedViewSet


class MenuItemViewSet(TenantScopedViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


class OrderViewSet(TenantScopedViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated, HasTenant]

    def get(self, request):
        tenant = request.user.tenant  # the only source of tenant in this view
        orders = Order.objects.filter(tenant=tenant)
        counts = dict(
            orders.exclude(shipment_status__isnull=True)
            .values_list("shipment_status")
            .annotate(n=Count("id"))
        )
        return Response(
            {
                "tenant": {
                    "name": tenant.name,
                    "locale": tenant.locale,
                    "currency": tenant.currency,
                    "timezone": tenant.timezone,
                },
                "recent_orders": OrderSerializer(
                    orders.order_by("-created_at")[:10], many=True
                ).data,
                "repeat_guest_rate": repeat_guest_rate(tenant),
                "failed_webhook_count": WebhookEvent.objects.filter(
                    tenant=tenant, status=WebhookEvent.Status.FAILED
                ).count(),
                "shipment_status_counts": {s: counts.get(s, 0) for s in Order.Shipment.values},
            }
        )
