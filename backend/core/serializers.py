from rest_framework import serializers

from .models import MenuItem, Order


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "name", "price_cents"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "customer_ref", "total_cents", "status", "shipment_status", "created_at"]
        read_only_fields = ["id", "shipment_status", "created_at"]
