from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from core.models import WebhookEvent
from core.webhooks import process

MAX_RETRIES = 3
STALE_AFTER = timedelta(minutes=5)


class Command(BaseCommand):
    help = "Retry failed (and stuck 'received') webhook events, up to 3 attempts each."

    def handle(self, *args, **opts):
        stuck = Q(status=WebhookEvent.Status.RECEIVED, created_at__lt=timezone.now() - STALE_AFTER)
        failed = Q(status=WebhookEvent.Status.FAILED)
        events = WebhookEvent.objects.filter(failed | stuck, retry_count__lt=MAX_RETRIES)
        ok = 0
        for event in events:
            event.retry_count += 1
            event.save(update_fields=["retry_count"])
            process(event)
            ok += event.status == WebhookEvent.Status.PROCESSED
        self.stdout.write(f"Retried {len(events)} event(s), {ok} recovered.")
