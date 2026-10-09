import json

from django.test import Client

from core.models import WebhookEvent
from core.webhooks import sign


def carrier(tenant, payload, event_id="car_1"):
    body = json.dumps(payload).encode()
    return Client().post(
        f"/api/webhooks/carrier/{tenant.id}/",
        data=body,
        content_type="application/json",
        HTTP_X_CARRIER_SIGNATURE=sign(tenant.webhook_secret, body),
        HTTP_X_CARRIER_EVENT_ID=event_id,
    )


def test_carrier_updates_shipment_status(tenant_a, order_a):
    r = carrier(tenant_a, {"order_id": order_a.id, "shipment_status": "in_transit"})
    assert r.status_code == 200
    order_a.refresh_from_db()
    assert order_a.shipment_status == "in_transit"


def test_carrier_cannot_touch_other_tenants_order(tenant_a, order_b):
    carrier(tenant_a, {"order_id": order_b.id, "shipment_status": "delivered"})
    order_b.refresh_from_db()
    assert order_b.shipment_status is None
    assert WebhookEvent.objects.get().status == "failed"


def test_carrier_unknown_status_fails(tenant_a, order_a):
    carrier(tenant_a, {"order_id": order_a.id, "shipment_status": "teleported"})
    assert WebhookEvent.objects.get().status == "failed"
