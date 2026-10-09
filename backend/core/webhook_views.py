import hmac

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Tenant, WebhookEvent
from .webhooks import SOURCES, process, sign


@csrf_exempt  # auth is the HMAC, not a session
@require_POST
def receive(request, source, tenant_id):
    cfg = SOURCES.get(source)
    tenant = Tenant.objects.filter(pk=tenant_id).first()
    if cfg is None or tenant is None:
        return HttpResponse(status=404)

    body = request.body  # raw bytes, read before any parsing
    expected = sign(tenant.webhook_secret, body)
    given = request.headers.get(cfg["sig"], "")
    if not hmac.compare_digest(expected.encode(), given.encode()):
        return HttpResponse(status=401)

    event_id = request.headers.get(cfg["id"])
    if not event_id:
        return HttpResponse(status=400)

    event, created = WebhookEvent.objects.get_or_create(
        tenant=tenant,
        source=source,
        event_id=event_id,
        defaults={"raw_payload": body.decode("utf-8", errors="replace")},
    )
    if created:
        process(event)
    return JsonResponse({"status": event.status})  # 200 for duplicates and failures alike
