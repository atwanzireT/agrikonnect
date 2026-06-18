from django.conf import settings
from django.db import models
from core.models import BaseModel


class MarketPrice(BaseModel):
    crop_name = models.CharField(max_length=100)
    variety = models.CharField(max_length=100, blank=True, null=True)
    market_name = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    price_date = models.DateField()
    min_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    average_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    source_name = models.CharField(max_length=255, blank=True, null=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="market_prices_entered"
    )

    class Meta:
        ordering = ["-price_date", "-created_at"]

    def __str__(self):
        return f"{self.crop_name} - {self.market_name} - {self.price_date}"


class CompanyProductPrice(BaseModel):
    """Prices offered by different buying companies for farm products."""

    UNIT_KG = "KG"
    UNIT_BAG = "BAG"
    UNIT_TONNE = "TONNE"
    UNIT_LITRE = "LITRE"
    UNIT_TRAY = "TRAY"
    UNIT_CRATE = "CRATE"
    UNIT_BUNCH = "BUNCH"
    UNIT_PIECE = "PIECE"

    UNIT_CHOICES = [
        (UNIT_KG, "Kilogram"),
        (UNIT_BAG, "Bag"),
        (UNIT_TONNE, "Tonne"),
        (UNIT_LITRE, "Litre"),
        (UNIT_TRAY, "Tray"),
        (UNIT_CRATE, "Crate"),
        (UNIT_BUNCH, "Bunch"),
        (UNIT_PIECE, "Piece"),
    ]

    product_name = models.CharField(max_length=120)
    variety = models.CharField(max_length=120, blank=True)
    company_name = models.CharField(max_length=160)
    district = models.CharField(max_length=120, blank=True)
    pickup_location = models.CharField(max_length=180, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default=UNIT_KG)
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_quantity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    quality_grade = models.CharField(max_length=80, blank=True)
    payment_terms = models.CharField(max_length=160, blank=True, help_text="Example: Cash on delivery, 7 days, mobile money")
    contact_person = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    price_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_product_prices_entered",
    )

    class Meta:
        ordering = ["product_name", "-price_per_unit", "company_name"]
        indexes = [
            models.Index(fields=["product_name", "district", "is_active"]),
            models.Index(fields=["company_name", "price_date"]),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.product_name} - {self.price_per_unit}/{self.unit}"
