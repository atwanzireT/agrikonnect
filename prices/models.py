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