import json
import random
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.metrics import repeat_guest_rate
from core.models import MenuItem, Order, Tenant, User, WebhookEvent

PASSWORD = "demo1234"

# Prices in major units; converted to integer cents below.
TENANTS = [
    {
        "name": "Parrilla Don Aníbal",
        "locale": "es-AR",
        "currency": "ARS",
        "timezone": "America/Argentina/Buenos_Aires",
        "webhook_secret": "whsec_parrilla_demo",
        "login": "parrilla@example.com",
        "customers": [
            "martin.gomez",
            "lucia.fernandez",
            "sofia.rodriguez",
            "joaquin.perez",
            "camila.sosa",
            "mateo.alvarez",
            "valentina.romero",
            "tomas.acosta",
            "agustina.torres",
            "facundo.diaz",
        ],
        "repeat_in": 4,
        "repeat_late": 1,
        "late_night": 4,
        "delivery_share": 0.5,
        "failed_events": ["malformed", "gave_up"],
        "menu": [
            ("Empanada de carne", 2800),
            ("Empanada de jamón y queso", 2800),
            ("Provoleta", 9500),
            ("Milanesa napolitana", 18500),
            ("Bife de chorizo", 24000),
            ("Flan con dulce de leche", 7500),
            ("Alfajor de maicena", 3200),
        ],
    },
    {
        "name": "Empanadas La Cañada",
        "locale": "es-AR",
        "currency": "ARS",
        "timezone": "America/Argentina/Cordoba",
        "webhook_secret": "whsec_empanaderia_demo",
        "login": "empanaderia@example.com",
        "customers": [
            "ana.molina",
            "bruno.castro",
            "carla.vega",
            "diego.ruiz",
            "elena.ortiz",
            "franco.silva",
            "julieta.rios",
            "nicolas.medina",
        ],
        "repeat_in": 2,
        "repeat_late": 1,
        "late_night": 0,
        "delivery_share": 0.6,
        "failed_events": [],
        "menu": [
            ("Empanada de carne cortada a cuchillo", 2600),
            ("Empanada de humita", 2600),
            ("Empanada de pollo", 2600),
            ("Empanada de verdura", 2400),
            ("Docena de empanadas", 29000),
            ("Alfajor cordobés", 3000),
            ("Gaseosa 500 ml", 2200),
        ],
    },
    {
        "name": "Café De Jordaan",
        "locale": "nl-NL",
        "currency": "EUR",
        "timezone": "Europe/Amsterdam",
        "webhook_secret": "whsec_cafe_demo",
        "login": "cafe@example.com",
        "customers": [
            "sanne.devries",
            "daan.jansen",
            "lotte.bakker",
            "jesse.visser",
            "emma.smit",
            "bram.meijer",
            "fleur.mulder",
            "thijs.deboer",
            "noor.bos",
            "luuk.vos",
        ],
        "repeat_in": 5,
        "repeat_late": 0,
        "late_night": 0,
        "delivery_share": 0.3,
        "failed_events": ["malformed"],
        "menu": [
            ("Koffie", 3.20),
            ("Cappuccino", 3.90),
            ("Uitsmijter ham/kaas", 11.50),
            ("Broodje kroket", 6.50),
            ("Appeltaart met slagroom", 5.50),
            ("Bitterballen (8 st.)", 9.00),
            ("Tosti ham/kaas", 6.00),
        ],
    },
]

SPECS = {s["name"]: s for s in TENANTS}


def local_dt(tz, days_ago, hour, minute, now):
    day = (now.astimezone(tz) - timedelta(days=days_ago)).date()
    return datetime.combine(day, time(hour, minute), tzinfo=tz)


def plan_orders(spec, rng, now, tz):
    """(customer, local datetime) pairs engineered so the repeat rate is known."""
    people = [f"{c}@example.com" for c in spec["customers"]]
    n_in, n_late = spec["repeat_in"], spec["repeat_late"]

    def at(days_ago, hour=None, minute=None):
        h = hour if hour is not None else rng.randint(11, 22)
        m = minute if minute is not None else rng.choice([0, 15, 30, 45])
        return local_dt(tz, days_ago, h, m, now)

    plan = []
    for ref in people[:n_in]:  # 2nd order 5-25 days after the 1st: counts
        first = rng.randint(30, 58)
        plan += [(ref, at(first)), (ref, at(first - rng.randint(5, 25)))]
    for ref in people[n_in : n_in + n_late]:  # 2nd order 41 days later: does not count
        plan += [(ref, at(55)), (ref, at(14))]
    for j, ref in enumerate(people[n_in + n_late :]):  # one order only
        if j < spec["late_night"]:
            plan.append((ref, at(rng.randint(5, 58), 23, 30)))  # 23:30 local = next day in UTC
        else:
            plan.append((ref, at(rng.randint(5, 58))))
    return plan


def create_orders(tenant, spec, rng, now):
    tz = ZoneInfo(tenant.timezone)
    menu = list(tenant.menu_items.order_by("id"))
    for ref, when in plan_orders(spec, rng, now, tz):
        items = rng.choices(menu, k=rng.randint(1, 4))
        age = (now - when).days
        pending = age < 10 and rng.random() < 0.4
        shipment = None  # dine-in stays null
        if rng.random() < spec["delivery_share"]:
            shipment = (
                "delivered" if age > 20 else rng.choice(["pending", "in_transit", "delivered"])
            )
        Order.objects.create(
            tenant=tenant,
            customer_ref=ref,
            total_cents=sum(i.price_cents for i in items),  # computed, not hardcoded
            status=Order.Status.PENDING if pending else Order.Status.COMPLETED,
            shipment_status=shipment,
            created_at=when,
        )


def create_webhook_events(tenant, spec, now):
    slug = spec["login"].split("@")[0]

    def make(key, payload, status, error="", retries=0, days_ago=1):
        WebhookEvent.objects.get_or_create(
            tenant=tenant,
            source="shop",
            event_id=f"{slug}_{key}",
            defaults={
                "raw_payload": payload,
                "status": status,
                "error": error,
                "retry_count": retries,
                "created_at": now - timedelta(days=days_ago),
            },
        )

    for n in (1, 2, 3):
        body = json.dumps({"customer_ref": f"guest{n}@example.com", "total_cents": 1000 * n})
        make(f"ok{n}", body, "processed", days_ago=n + 1)
    for kind in spec["failed_events"]:
        if kind == "malformed":
            make("bad", "not json{", "failed", "JSONDecodeError: Expecting value: line 1 column 1")
        else:  # retried 3 times, gave up
            make(
                "gaveup",
                '{"customer_ref": "x@example.com"}',
                "failed",
                "KeyError: 'total_cents'",
                3,
                4,
            )


class Command(BaseCommand):
    help = "Seed demo tenants, logins, menus, orders and webhook events. Safe to re-run."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Wipe demo data first")

    @transaction.atomic
    def handle(self, *args, **opts):
        now = timezone.now()

        if opts["flush"]:
            User.objects.filter(tenant__isnull=False).delete()  # FK is PROTECT: users first
            Tenant.objects.all().delete()  # cascades menu items, orders, webhook events

        for idx, spec in enumerate(TENANTS):
            tenant, _ = Tenant.objects.update_or_create(
                name=spec["name"],
                defaults={k: spec[k] for k in ("locale", "currency", "timezone", "webhook_secret")},
            )
            user, created = User.objects.get_or_create(
                username=spec["login"], defaults={"email": spec["login"], "tenant": tenant}
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            for name, price in spec["menu"]:
                MenuItem.objects.update_or_create(
                    tenant=tenant, name=name, defaults={"price_cents": round(price * 100)}
                )
            if not tenant.orders.exists():  # re-run safe
                create_orders(tenant, spec, random.Random(42 + idx), now)
            create_webhook_events(tenant, spec, now)

        self.stdout.write(self.style.SUCCESS("Seeded."))
        for t in Tenant.objects.order_by("id"):
            spec = SPECS[t.name]
            expected = spec["repeat_in"] / len(spec["customers"])
            self.stdout.write(
                f"  {t.name:<22} {t.orders.count():>2} orders  "
                f"repeat {repeat_guest_rate(t):.0%} (expected {expected:.0%})  "
                f"login: {t.users.first().username} / {PASSWORD}"
            )
