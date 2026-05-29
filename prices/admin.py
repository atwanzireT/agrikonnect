from django.contrib import admin

from .models import MarketPrice


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = (
        "crop_name",
        "variety",
        "market_name",
        "district",
        "price_date",
        "min_price",
        "max_price",
        "average_price",
        "source_name",
        "entered_by",
    )
    list_filter = ("district", "market_name", "price_date", "created_at")
    search_fields = (
        "crop_name",
        "variety",
        "market_name",
        "district",
        "source_name",
        "entered_by__full_name",
    )
    autocomplete_fields = ("entered_by",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-price_date", "-created_at")