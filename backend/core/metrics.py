from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db.models import Count
from django.db.models.functions import TruncDate

from .models import Order

REPEAT_WINDOW = timedelta(days=30)


def repeat_guest_rate(tenant) -> float:
    """Guests whose 2nd order came within 30 days of their 1st, over guests with >=1 order."""
    rows = (
        Order.objects.filter(tenant=tenant)
        .order_by("created_at")
        .values_list("customer_ref", "created_at")
    )
    by_guest: dict[str, list] = {}
    for ref, ts in rows:
        by_guest.setdefault(ref, []).append(ts)
    if not by_guest:
        return 0.0
    repeats = sum(1 for t in by_guest.values() if len(t) > 1 and t[1] - t[0] <= REPEAT_WINDOW)
    return repeats / len(by_guest)


def orders_per_day(tenant) -> dict:
    """Day buckets in the tenant's timezone, not the server's."""
    day = TruncDate("created_at", tzinfo=ZoneInfo(tenant.timezone))
    qs = (
        Order.objects.filter(tenant=tenant)
        .annotate(day=day)
        .values("day")
        .annotate(n=Count("id"))
        .order_by("day")
    )
    return {r["day"]: r["n"] for r in qs}
