from django import forms
from .models import FarmerProfile, BusinessProfile, BusinessVerificationDocument
from core.forms import apply_tailwind_classes


class FarmerProfileForm(forms.ModelForm):
    class Meta:
        model = FarmerProfile
        fields = [
            "national_id",
            "gender",
            "date_of_birth",
            "village",
            "subcounty",
            "district",
            "primary_crop",
            "farming_experience_years",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = [
            "business_name",
            "contact_person",
            "business_type",
            "registration_number",
            "tin_number",
            "district",
            "physical_address",
            "website",
        ]
        widgets = {
            "physical_address": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)


class BusinessVerificationDocumentForm(forms.ModelForm):
    class Meta:
        model = BusinessVerificationDocument
        fields = ["document_type", "file", "review_note"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)