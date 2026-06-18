from django import forms
from django.utils import timezone

from .models import CompanyProductPrice, MarketPrice
from core.forms import apply_tailwind_classes


class MarketPriceForm(forms.ModelForm):
    class Meta:
        model = MarketPrice
        fields = [
            "crop_name",
            "variety",
            "market_name",
            "district",
            "price_date",
            "min_price",
            "max_price",
            "average_price",
            "source_name",
        ]
        widgets = {
            "price_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)


class CompanyProductPriceForm(forms.ModelForm):
    class Meta:
        model = CompanyProductPrice
        fields = [
            "product_name",
            "variety",
            "company_name",
            "district",
            "pickup_location",
            "unit",
            "price_per_unit",
            "minimum_quantity",
            "quality_grade",
            "payment_terms",
            "contact_person",
            "phone_number",
            "price_date",
            "is_active",
            "notes",
        ]
        widgets = {
            "price_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("price_date") and not self.instance.pk:
            self.initial["price_date"] = timezone.localdate()
        apply_tailwind_classes(self)
