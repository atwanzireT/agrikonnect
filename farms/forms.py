from django import forms
from django.utils import timezone

from .models import Farm, FarmProject, HarvestRecord, FarmExpense, SalesRecord
from core.forms import apply_tailwind_classes


DEFAULT_PROJECT_OPTIONS = [
    "Maize", "Coffee", "Bananas", "Beans", "Vegetables",
    "Dairy", "Poultry", "Piggery", "Goats", "Fish farming", "Apiary",
]


class FarmForm(forms.ModelForm):
    project_names = forms.CharField(
        required=False,
        label="Main farm projects",
        help_text="Enter one or more farm projects separated by commas. Example: Maize Season A, Coffee, Poultry Layers.",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Maize, Coffee, Dairy, Poultry"}),
    )

    class Meta:
        model = Farm
        fields = [
            "farm_name", "district", "subcounty", "village", "acreage",
            "soil_type", "water_source", "project_names",
        ]
        widgets = {
            "farm_name": forms.TextInput(attrs={"placeholder": "e.g., Green Acres Farm"}),
            "district": forms.TextInput(attrs={"placeholder": "e.g., Kampala"}),
            "subcounty": forms.TextInput(attrs={"placeholder": "e.g., Central Division"}),
            "village": forms.TextInput(attrs={"placeholder": "e.g., Bukoto"}),
            "acreage": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01"}),
        }

    def __init__(self, *args, farmer=None, **kwargs):
        self.farmer = farmer
        super().__init__(*args, **kwargs)
        if farmer:
            self.instance.farmer = farmer
        if self.instance and self.instance.pk and not self.initial.get("project_names"):
            self.initial["project_names"] = ", ".join(self.instance.projects.values_list("name", flat=True))
        apply_tailwind_classes(self)


    def _post_clean(self):
        # ModelForm calls model.full_clean() during is_valid().
        # Farm.clean() needs a farmer, so attach the logged-in user before validation.
        if self.farmer:
            self.instance.farmer = self.farmer
        super()._post_clean()

    def project_name_list(self):
        raw = self.cleaned_data.get("project_names") or ""
        names = []
        for item in raw.replace("\n", ",").split(","):
            name = item.strip()
            if name and name.lower() not in [n.lower() for n in names]:
                names.append(name)
        return names

    def save_projects(self, farm, farmer):
        for name in self.project_name_list():
            FarmProject.objects.get_or_create(
                farm=farm,
                farmer=farmer,
                name=name,
                defaults={
                    "project_type": FarmProject._meta.get_field("project_type").default,
                    "start_date": timezone.localdate(),
                    "status": "active",
                },
            )


class FarmProjectForm(forms.ModelForm):
    class Meta:
        model = FarmProject
        fields = [
            "farm", "name", "project_type", "acreage", "description",
            "start_date", "expected_end_date", "status", "expected_revenue",
            "expected_cost", "target_quantity", "target_unit", "notes",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "expected_end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, farmer=None, farm=None, **kwargs):
        self.farmer = farmer
        self.selected_farm = farm
        super().__init__(*args, **kwargs)
        if farmer:
            self.instance.farmer = farmer
        if farm:
            self.instance.farm = farm
        if farmer:
            self.fields["farm"].queryset = Farm.objects.filter(farmer=farmer).order_by("farm_name")
        if farm:
            self.fields["farm"].initial = farm
            self.fields["farm"].widget = forms.HiddenInput()
        if not self.initial.get("start_date") and not self.instance.pk:
            self.initial["start_date"] = timezone.localdate()
        apply_tailwind_classes(self)


    def _post_clean(self):
        # Attach required relations before Django calls model.full_clean().
        # This prevents RelatedObjectDoesNotExist during form.is_valid().
        if self.farmer:
            self.instance.farmer = self.farmer
        farm = self.cleaned_data.get("farm") if hasattr(self, "cleaned_data") else None
        if self.selected_farm:
            self.instance.farm = self.selected_farm
        elif farm:
            self.instance.farm = farm
        super()._post_clean()

    def clean_farm(self):
        farm = self.cleaned_data.get("farm") or self.selected_farm
        if self.farmer and farm and farm.farmer_id != self.farmer.id:
            raise forms.ValidationError("Choose one of your own farms.")
        return farm

    def clean_name(self):
        return (self.cleaned_data.get("name") or "").strip()

    def clean(self):
        cleaned = super().clean()
        farm = cleaned.get("farm")
        name = cleaned.get("name")
        if farm and name:
            qs = FarmProject.objects.filter(farm=farm, farmer=self.farmer, name__iexact=name, is_deleted=False)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("name", "This project already exists on the selected farm.")
        return cleaned


class ProjectScopedFormMixin:
    def __init__(self, *args, farmer=None, **kwargs):
        self.farmer = farmer
        super().__init__(*args, **kwargs)
        if farmer:
            self.instance.farmer = farmer
        if farmer:
            farms = Farm.objects.filter(farmer=farmer)
            projects = FarmProject.objects.filter(farmer=farmer, is_deleted=False).select_related("farm")
            if "farm" in self.fields:
                self.fields["farm"].queryset = farms
            if "project" in self.fields:
                self.fields["project"].queryset = projects
                self.fields["project"].required = True
                self.fields["project"].help_text = "Choose the farm project/product this record belongs to."
        apply_tailwind_classes(self)


    def _post_clean(self):
        # Attach farmer/farm before model.full_clean(), because the model
        # validators compare farmer, farm, and project ownership.
        if self.farmer:
            self.instance.farmer = self.farmer
        project = self.cleaned_data.get("project") if hasattr(self, "cleaned_data") else None
        farm = self.cleaned_data.get("farm") if hasattr(self, "cleaned_data") else None
        if project:
            self.instance.project = project
            self.instance.farm = project.farm
        elif farm:
            self.instance.farm = farm
        super()._post_clean()

    def clean(self):
        cleaned = super().clean()
        project = cleaned.get("project")
        farm = cleaned.get("farm")
        if project:
            cleaned["farm"] = project.farm
            if farm and farm != project.farm:
                self.add_error("farm", "Farm must match the selected project.")
        return cleaned


class HarvestRecordForm(ProjectScopedFormMixin, forms.ModelForm):
    class Meta:
        model = HarvestRecord
        fields = [
            "project", "farm", "crop_name", "variety", "season", "acreage_used",
            "expected_yield", "actual_yield", "unit", "harvest_date", "notes",
        ]
        labels = {"crop_name": "Product / output name", "actual_yield": "Actual quantity"}
        widgets = {"harvest_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 4})}


class FarmExpenseForm(ProjectScopedFormMixin, forms.ModelForm):
    class Meta:
        model = FarmExpense
        fields = ["project", "farm", "expense_date", "category", "description", "amount", "season", "receipt_number"]
        widgets = {"expense_date": forms.DateInput(attrs={"type": "date"}), "description": forms.Textarea(attrs={"rows": 4})}


class SalesRecordForm(ProjectScopedFormMixin, forms.ModelForm):
    class Meta:
        model = SalesRecord
        fields = [
            "project", "farm", "harvest", "crop_name", "quantity", "unit", "price_per_unit",
            "buyer_name", "sale_channel", "sale_date", "notes",
        ]
        labels = {"crop_name": "Product sold"}
        widgets = {"sale_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, farmer=None, **kwargs):
        super().__init__(*args, farmer=farmer, **kwargs)
        if farmer:
            self.fields["harvest"].queryset = HarvestRecord.objects.filter(farmer=farmer, is_deleted=False).select_related("project", "farm")
