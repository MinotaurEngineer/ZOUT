import pytest
from rest_framework.test import APIClient

from core.models import Order, Tenant, User


def _tenant(name, locale, currency, tz):
    return Tenant.objects.create(
        name=name, locale=locale, currency=currency, timezone=tz, webhook_secret=f"whsec_{name}"
    )


@pytest.fixture
def tenant_a(db):
    return _tenant("a", "es-AR", "ARS", "America/Argentina/Buenos_Aires")


@pytest.fixture
def tenant_b(db):
    return _tenant("b", "nl-NL", "EUR", "Europe/Amsterdam")


@pytest.fixture
def user_a(tenant_a):
    return User.objects.create_user("a@example.com", password="demo1234", tenant=tenant_a)


@pytest.fixture
def user_b(tenant_b):
    return User.objects.create_user("b@example.com", password="demo1234", tenant=tenant_b)


@pytest.fixture
def client_a(user_a):
    c = APIClient()
    c.force_authenticate(user_a)
    return c


@pytest.fixture
def order_a(tenant_a):
    return Order.objects.create(tenant=tenant_a, customer_ref="x@example.com", total_cents=1000)


@pytest.fixture
def order_b(tenant_b):
    return Order.objects.create(tenant=tenant_b, customer_ref="y@example.com", total_cents=2000)
