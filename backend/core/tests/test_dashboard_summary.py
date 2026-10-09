from core.models import Order, WebhookEvent


def _failed(tenant, event_id):
    return WebhookEvent.objects.create(
        tenant=tenant, source="shop", event_id=event_id, raw_payload="x", status="failed"
    )


def test_summary_only_reflects_own_tenant(client_a, tenant_a, tenant_b, order_a, order_b):
    Order.objects.filter(pk=order_a.pk).update(shipment_status="in_transit")
    Order.objects.filter(pk=order_b.pk).update(shipment_status="delivered")
    _failed(tenant_a, "1")
    _failed(tenant_b, "2")
    _failed(tenant_b, "3")

    data = client_a.get("/api/dashboard/summary/").json()

    assert [o["id"] for o in data["recent_orders"]] == [order_a.id]
    assert data["failed_webhook_count"] == 1
    assert data["shipment_status_counts"] == {"pending": 0, "in_transit": 1, "delivered": 0}
    assert data["tenant"]["currency"] == "ARS"


def test_summary_zero_state(client_a):
    data = client_a.get("/api/dashboard/summary/").json()
    assert data["recent_orders"] == []
    assert data["repeat_guest_rate"] == 0.0
    assert data["failed_webhook_count"] == 0
    assert data["shipment_status_counts"] == {"pending": 0, "in_transit": 0, "delivered": 0}
