from datetime import date, datetime, timedelta, timezone

from core.metrics import orders_per_day, repeat_guest_rate
from core.models import Order

BASE = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


def order(tenant, ref, day):
    return Order.objects.create(
        tenant=tenant, customer_ref=ref, total_cents=1000, created_at=BASE + timedelta(days=day)
    )


def test_no_orders_is_zero(tenant_a):
    assert repeat_guest_rate(tenant_a) == 0.0


def test_zero_repeats(tenant_a):
    order(tenant_a, "a", 0)
    order(tenant_a, "b", 1)
    assert repeat_guest_rate(tenant_a) == 0.0


def test_repeat_inside_30_days(tenant_a):
    order(tenant_a, "a", 0)
    order(tenant_a, "a", 10)
    order(tenant_a, "b", 0)
    assert repeat_guest_rate(tenant_a) == 0.5


def test_repeat_outside_30_days_does_not_count(tenant_a):
    order(tenant_a, "a", 0)
    order(tenant_a, "a", 40)
    assert repeat_guest_rate(tenant_a) == 0.0


def test_exactly_30_days_counts(tenant_a):
    order(tenant_a, "a", 0)
    order(tenant_a, "a", 30)
    assert repeat_guest_rate(tenant_a) == 1.0


def test_mixed(tenant_a):
    order(tenant_a, "a", 0)
    order(tenant_a, "a", 10)  # repeat
    order(tenant_a, "b", 0)
    order(tenant_a, "b", 40)  # too late
    order(tenant_a, "c", 5)
    order(tenant_a, "d", 6)
    assert repeat_guest_rate(tenant_a) == 0.25


def test_other_tenants_orders_are_ignored(tenant_a, tenant_b):
    order(tenant_b, "a", 0)
    order(tenant_b, "a", 5)
    order(tenant_a, "a", 0)
    assert repeat_guest_rate(tenant_a) == 0.0


def test_orders_group_by_tenant_timezone(tenant_a):
    # 23:30 in Buenos Aires on 1 June is 02:30 UTC on 2 June.
    Order.objects.create(
        tenant=tenant_a,
        customer_ref="x",
        total_cents=1,
        created_at=datetime(2026, 6, 2, 2, 30, tzinfo=timezone.utc),
    )
    assert orders_per_day(tenant_a) == {date(2026, 6, 1): 1}
