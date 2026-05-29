from django import forms
from .models import Farm, HarvestRecord, FarmExpense, SalesRecord
from core.forms import apply_tailwind_classes



class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['farm_name', 'district', 'subcounty', 'village', 'acreage', 'main_crop']
        widgets = {
            'farm_name': forms.TextInput(attrs={
                'placeholder': 'e.g., Green Acres Farm',
                'class': 'focus:ring-2 focus:ring-green-500'
            }),
            'district': forms.TextInput(attrs={
                'placeholder': 'e.g., Kampala',
                'class': 'focus:ring-2 focus:ring-green-500'
            }),
            'subcounty': forms.TextInput(attrs={
                'placeholder': 'e.g., Central Division',
                'class': 'focus:ring-2 focus:ring-green-500'
            }),
            'village': forms.TextInput(attrs={
                'placeholder': 'e.g., Bukoto',
                'class': 'focus:ring-2 focus:ring-green-500'
            }),
            'acreage': forms.NumberInput(attrs={
                'placeholder': '0.00',
                'step': '0.01',
                'class': 'focus:ring-2 focus:ring-green-500'
            }),
            'main_crop': forms.TextInput(attrs={
                'placeholder': 'e.g., Maize, Coffee, Beans',
                'class': 'focus:ring-2 focus:ring-green-500'
            }),
        }


class HarvestRecordForm(forms.ModelForm):
    class Meta:
        model = HarvestRecord
        fields = [
            "farm",
            "crop_name",
            "variety",
            "season",
            "acreage_used",
            "expected_yield",
            "actual_yield",
            "unit",
            "harvest_date",
            "notes",
        ]
        widgets = {
            "harvest_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if farmer:
            self.fields["farm"].queryset = Farm.objects.filter(farmer=farmer)
        apply_tailwind_classes(self)


class FarmExpenseForm(forms.ModelForm):
    class Meta:
        model = FarmExpense
        fields = [
            "farm",
            "expense_date",
            "category",
            "description",
            "amount",
            "season",
            "receipt_number",
        ]
        widgets = {
            "expense_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if farmer:
            self.fields["farm"].queryset = Farm.objects.filter(farmer=farmer)
        apply_tailwind_classes(self)


class SalesRecordForm(forms.ModelForm):
    class Meta:
        model = SalesRecord
        fields = [
            "farm",
            "crop_name",
            "quantity",
            "unit",
            "price_per_unit",
            "buyer_name",
            "sale_channel",
            "sale_date",
            "notes",
        ]
        widgets = {
            "sale_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if farmer:
            self.fields["farm"].queryset = Farm.objects.filter(farmer=farmer)
        apply_tailwind_classes(self)