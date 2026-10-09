from django.core.management import call_command

from core.models import MenuItem, Tenant, User


def test_seed_is_idempotent(db):
    call_command("seed")
    counts = (Tenant.objects.count(), User.objects.count(), MenuItem.objects.count())
    call_command("seed")
    assert (Tenant.objects.count(), User.objects.count(), MenuItem.objects.count()) == counts
    assert counts == (3, 3, 21)
