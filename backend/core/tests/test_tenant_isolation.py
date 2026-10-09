import pytest
from rest_framework.test import APIClient

from core.models import Order


def test_a_cannot_list_bs_orders(client_a, order_a, order_b):
    r = client_a.get("/api/orders/")
    assert r.status_code == 200
    assert [o["id"] for o in r.json()] == [order_a.id]


def test_a_gets_404_for_bs_order(client_a, order_b):
    assert client_a.get(f"/api/orders/{order_b.id}/").status_code == 404


def test_create_ignores_tenant_in_body(client_a, tenant_a, tenant_b):
    r = client_a.post(
        "/api/orders/",
        {"customer_ref": "z@example.com", "total_cents": 500, "tenant": tenant_b.id},
        format="json",
    )
    assert r.status_code == 201
    assert Order.objects.get(id=r.json()["id"]).tenant == tenant_a
    assert not Order.objects.filter(tenant=tenant_b).exists()


@pytest.mark.django_db
def test_unauthenticated_is_401():
    assert APIClient().get("/api/orders/").status_code == 401


def test_jwt_login_then_access(user_a, order_a):
    c = APIClient()
    r = c.post("/api/token/", {"username": "a@example.com", "password": "demo1234"}, format="json")
    assert r.status_code == 200
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['access']}")
    assert c.get("/api/orders/").status_code == 200
