from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    name = models.CharField(max_length=200)
    locale = models.CharField(max_length=10)  # es-AR, nl-NL
    currency = models.CharField(max_length=3)  # ARS, EUR
    timezone = models.CharField(max_length=64)  # IANA name
    webhook_secret = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class User(AbstractUser):
    # Nullable only so createsuperuser works; every real user has a tenant.
    tenant = models.ForeignKey(Tenant, null=True, on_delete=models.PROTECT, related_name="users")


class MenuItem(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=200)
    price_cents = models.PositiveIntegerField()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        COMPLETED = "completed"

    class Shipment(models.TextChoices):
        PENDING = "pending"
        IN_TRANSIT = "in_transit"
        DELIVERED = "delivered"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="orders")
    customer_ref = models.CharField(max_length=200)  # customer email
    total_cents = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    shipment_status = models.CharField(
        max_length=20, choices=Shipment.choices, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)  # not auto_now_add: seed backdates

    class Meta:
        indexes = [models.Index(fields=["tenant", "created_at"])]


class WebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received"
        PROCESSED = "processed"
        FAILED = "failed"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="webhook_events")
    source = models.CharField(max_length=20)  # "shop" | "carrier"
    event_id = models.CharField(max_length=200)
    raw_payload = models.TextField()  # the exact body that was signed
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    error = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "source", "event_id"], name="uniq_webhook_event"
            )
        ]
