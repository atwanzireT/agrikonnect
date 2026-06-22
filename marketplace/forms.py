from django import forms
from .models import (
    ProduceListing,
    ProduceListingImage,
    ListingInquiry,
    BuyerRequest,
    BuyerRequestImage,
    MarketplacePurchase,
)
from farms.models import Farm
from core.forms import apply_tailwind_classes


class ProduceListingForm(forms.ModelForm):
    class Meta:
        model = ProduceListing
        fields = [
            "farm",
            "crop_name",
            "variety",
            "quality",
            "quantity",
            "unit",
            "expected_price",
            "district",
            "subcounty",
            "village",
            "latitude",
            "longitude",
            "available_from",
            "status",
            "description",
        ]
        widgets = {
            "available_from": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if farmer:
            self.fields["farm"].queryset = Farm.objects.filter(farmer=farmer)

        self.fields["crop_name"].label = "Product name"
        self.fields["crop_name"].widget.attrs.setdefault("placeholder", "e.g. Maize, Beans, Matooke")
        self.fields["description"].label = "Product description"
        self.fields["description"].help_text = "Describe quality, harvest date, packaging, storage condition, delivery options, and anything buyers should know."
        self.fields["description"].widget.attrs.setdefault("placeholder", "Example: Freshly harvested maize, clean and dry, packed in 100kg bags, available for pickup in Mbarara...")
        self.fields["status"].initial = "open"
        apply_tailwind_classes(self)


class ProduceListingImageForm(forms.ModelForm):
    class Meta:
        model = ProduceListingImage
        fields = ["image", "is_primary", "sort_order"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)


class ListingInquiryForm(forms.ModelForm):
    class Meta:
        model = ListingInquiry
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)


class BuyerRequestForm(forms.ModelForm):
    class Meta:
        model = BuyerRequest
        fields = [
            "crop_name",
            "variety",
            "quantity_needed",
            "unit",
            "min_price",
            "max_price",
            "delivery_district",
            "delivery_location",
            "latitude",
            "longitude",
            "date_needed",
            "status",
            "notes",
        ]
        widgets = {
            "date_needed": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)


class BuyerRequestImageForm(forms.ModelForm):
    class Meta:
        model = BuyerRequestImage
        fields = ["image", "is_primary", "sort_order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)

class MarketplacePurchaseForm(forms.ModelForm):
    class Meta:
        model = MarketplacePurchase
        fields = ["quantity", "delivery_location", "buyer_phone", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)
