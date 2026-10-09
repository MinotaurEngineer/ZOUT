from zoneinfo import ZoneInfo

from django.core.management import call_command

from core.metrics import orders_per_day, repeat_guest_rate
from core.models import MenuItem, Order, Tenant, User, WebhookEvent


def _counts():
    models = (Tenant, User, MenuItem, Order, WebhookEvent)
    return tuple(m.objects.count() for m in models)


def test_seed_is_idempotent(db):
    call_command("seed")
    first = _counts()
    call_command("seed")
    assert _counts() == first
    assert first[:3] == (3, 3, 21)


def test_seeded_repeat_rates_match_spec(db):
    call_command("seed")
    rates = {t.name: repeat_guest_rate(t) for t in Tenant.objects.all()}
    assert rates == {
        "Parrilla Don Aníbal": 0.4,
        "Empanadas La Cañada": 0.25,
        "Café De Jordaan": 0.5,
    }


def test_late_night_orders_land_on_local_day(db):
    call_command("seed")
    t = Tenant.objects.get(name__startswith="Parrilla")
    tz = ZoneInfo(t.timezone)
    late = [o for o in t.orders.all() if o.created_at.astimezone(tz).strftime("%H:%M") == "23:30"]
    assert len(late) == 4
    per_day = orders_per_day(t)
    for o in late:
        local_day = o.created_at.astimezone(tz).date()
        assert o.created_at.date() != local_day  # UTC calendar says "tomorrow"
        assert per_day[local_day] >= 1
