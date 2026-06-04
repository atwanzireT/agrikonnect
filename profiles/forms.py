from django import forms
from .models import FarmerProfile, BusinessProfile, BusinessVerificationDocument
from core.forms import apply_tailwind_classes


TAILWIND_INPUT = """
w-full rounded-2xl border border-gray-200 bg-white px-4 py-3
text-gray-800 shadow-sm transition duration-200
focus:border-green-500 focus:ring-4 focus:ring-green-100
placeholder:text-gray-400
"""

TAILWIND_SELECT = """
w-full rounded-2xl border border-gray-200 bg-white px-4 py-3
text-gray-800 shadow-sm transition duration-200
focus:border-green-500 focus:ring-4 focus:ring-green-100
"""

TAILWIND_TEXTAREA = """
w-full rounded-2xl border border-gray-200 bg-white px-4 py-3
text-gray-800 shadow-sm transition duration-200
focus:border-green-500 focus:ring-4 focus:ring-green-100
placeholder:text-gray-400
"""

TAILWIND_FILE = """
block w-full rounded-2xl border-2 border-dashed border-green-200
bg-green-50 p-4 text-sm text-gray-700
file:mr-4 file:rounded-xl file:border-0
file:bg-green-700 file:px-4 file:py-2
file:text-white file:font-semibold
hover:border-green-400
"""


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
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": TAILWIND_INPUT,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_tailwind_classes(self)

        self.fields["national_id"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Enter National ID Number",
        })

        self.fields["gender"].widget.attrs.update({
            "class": TAILWIND_SELECT,
        })

        self.fields["village"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Village",
        })

        self.fields["subcounty"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Subcounty",
        })

        self.fields["district"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "District",
        })

        self.fields["primary_crop"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Primary Crop",
        })

        self.fields["farming_experience_years"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Years of Experience",
        })


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
            "physical_address": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": TAILWIND_TEXTAREA,
                    "placeholder": "Business Address",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_tailwind_classes(self)

        self.fields["business_name"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Business Name",
        })

        self.fields["contact_person"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Contact Person",
        })

        self.fields["business_type"].widget.attrs.update({
            "class": TAILWIND_SELECT,
        })

        self.fields["registration_number"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "Registration Number",
        })

        self.fields["tin_number"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "TIN Number",
        })

        self.fields["district"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "District",
        })

        self.fields["website"].widget.attrs.update({
            "class": TAILWIND_INPUT,
            "placeholder": "https://yourbusiness.com",
        })


class BusinessVerificationDocumentForm(forms.ModelForm):
    class Meta:
        model = BusinessVerificationDocument
        fields = [
            "document_type",
            "file",
            "review_note",
        ]
        widgets = {
            "review_note": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": TAILWIND_TEXTAREA,
                    "placeholder": "Optional note about this document...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_tailwind_classes(self)

        self.fields["document_type"].widget.attrs.update({
            "class": TAILWIND_SELECT,
        })

        self.fields["file"].widget.attrs.update({
            "class": TAILWIND_FILE,
        })

        self.fields["review_note"].required = False

        self.fields["document_type"].label = "Document Type"
        self.fields["file"].label = "Upload Document"
        self.fields["review_note"].label = "Additional Notes"