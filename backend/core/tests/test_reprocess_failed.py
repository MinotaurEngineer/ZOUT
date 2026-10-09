import json
from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone

from core.models import Order, WebhookEvent


def _failed_event(tenant, retry_count=0):
    payload = json.dumps({"customer_ref": "r@example.com", "total_cents": 900})
    return WebhookEvent.objects.create(
        tenant=tenant,
        source="shop",
        event_id="evt_r",
        raw_payload=payload,
        status="failed",
        error="transient",
        retry_count=retry_count,
    )


def test_reprocess_recovers_transient_failure(tenant_a):
    event = _failed_event(tenant_a)
    call_command("reprocess_failed")
    event.refresh_from_db()
    assert (event.status, event.retry_count) == ("processed", 1)
    assert Order.objects.count() == 1


def test_reprocess_gives_up_after_three(tenant_a):
    event = _failed_event(tenant_a, retry_count=3)
    call_command("reprocess_failed")
    event.refresh_from_db()
    assert (event.status, event.retry_count) == ("failed", 3)
    assert not Order.objects.exists()


def test_reprocess_picks_up_stuck_received_event(tenant_a):
    event = _failed_event(tenant_a)
    WebhookEvent.objects.filter(pk=event.pk).update(
        status="received", created_at=timezone.now() - timedelta(minutes=10)
    )
    call_command("reprocess_failed")
    event.refresh_from_db()
    assert event.status == "processed"
