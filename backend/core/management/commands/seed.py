import random

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import MenuItem, Tenant, User

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


class Command(BaseCommand):
    help = "Seed demo tenants, logins and menus. Safe to re-run; --flush rebuilds."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Wipe demo data first")

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(42)  # deterministic; used by the Day 3 order generator
        if opts["flush"]:
            User.objects.filter(tenant__isnull=False).delete()  # FK is PROTECT: users first
            Tenant.objects.all().delete()  # cascades menu items and orders

        for spec in TENANTS:
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

        self.stdout.write(self.style.SUCCESS("Seeded."))
        for t in Tenant.objects.order_by("id"):
            login = t.users.first().username
            self.stdout.write(
                f"  {t.name:<22} {t.currency} {t.timezone:<32} "
                f"{t.menu_items.count()} items  login: {login} / {PASSWORD}"
            )
