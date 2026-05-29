from django import forms
from .models import MarketPrice
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