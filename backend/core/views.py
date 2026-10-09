from .models import MenuItem, Order
from .serializers import MenuItemSerializer, OrderSerializer
from .viewsets import TenantScopedViewSet


class MenuItemViewSet(TenantScopedViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


class OrderViewSet(TenantScopedViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
