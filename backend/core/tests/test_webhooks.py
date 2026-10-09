import json

import pytest
from django.test import Client

from core.models import Order, WebhookEvent
from core.webhooks import sign

GOOD = json.dumps({"customer_ref": "m@example.com", "total_cents": 1500}).encode()


def post(tenant, body=GOOD, event_id="evt_1", secret=None):
    return Client().post(
        f"/api/webhooks/shop/{tenant.id}/",
        data=body,
        content_type="application/json",
        HTTP_X_SHOPIFY_HMAC_SHA256=sign(secret or tenant.webhook_secret, body),
        HTTP_X_SHOPIFY_WEBHOOK_ID=event_id,
    )


def test_valid_event_creates_order(tenant_a):
    assert post(tenant_a).status_code == 200
    order = Order.objects.get()
    assert (order.tenant, order.total_cents) == (tenant_a, 1500)
    assert WebhookEvent.objects.get().status == "processed"


def test_duplicate_event_creates_one_order(tenant_a):
    assert post(tenant_a).status_code == 200
    assert post(tenant_a).status_code == 200
    assert Order.objects.count() == 1
    assert WebhookEvent.objects.count() == 1


def test_bad_signature_is_401_and_stores_nothing(tenant_a):
    assert post(tenant_a, secret="wrong").status_code == 401
    assert not Order.objects.exists()
    assert not WebhookEvent.objects.exists()


def test_other_tenants_secret_is_rejected(tenant_a, tenant_b):
    assert post(tenant_b, secret=tenant_a.webhook_secret).status_code == 401


@pytest.mark.parametrize(
    "body", [b"not json", b'{"customer_ref": "x"}', b'{"customer_ref": "x", "total_cents": -5}']
)
def test_malformed_payload_is_failed_but_200(tenant_a, body):
    assert post(tenant_a, body=body).status_code == 200
    event = WebhookEvent.objects.get()
    assert event.status == "failed"
    assert event.error
    assert not Order.objects.exists()
