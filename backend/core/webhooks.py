import base64
import hashlib
import hmac
import json

from django.db import transaction

from .models import Order, WebhookEvent

SOURCES = {
    "shop": {"sig": "X-Shopify-Hmac-Sha256", "id": "X-Shopify-Webhook-Id"},
    "carrier": {"sig": "X-Carrier-Signature", "id": "X-Carrier-Event-Id"},
}


def sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def handle_shop(event: WebhookEvent) -> None:
    data = json.loads(event.raw_payload)
    Order.objects.create(
        tenant=event.tenant,
        customer_ref=data["customer_ref"],
        total_cents=int(data["total_cents"]),
    )


def handle_carrier(event: WebhookEvent) -> None:
    data = json.loads(event.raw_payload)
    status = data["shipment_status"]
    if status not in Order.Shipment.values:
        raise ValueError(f"unknown shipment_status {status!r}")
    # Scoped to the event's tenant: a carrier event can never touch another tenant's order.
    order = Order.objects.get(tenant=event.tenant, pk=data["order_id"])
    order.shipment_status = status
    order.save(update_fields=["shipment_status"])


HANDLERS = {"shop": handle_shop, "carrier": handle_carrier}


def process(event: WebhookEvent) -> None:
    """Order creation and the 'processed' flag commit together, or neither does."""
    try:
        with transaction.atomic():
            HANDLERS[event.source](event)
            event.status = WebhookEvent.Status.PROCESSED
            event.error = ""
            event.save(update_fields=["status", "error"])
    except Exception as exc:  # any failure is recorded, never raised to the sender
        event.status = WebhookEvent.Status.FAILED
        event.error = f"{type(exc).__name__}: {exc}"
        event.save(update_fields=["status", "error"])
