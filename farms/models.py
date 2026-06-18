from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel


class SaleChannelChoices(models.TextChoices):
    MARKET = "market", "Market"
    DIRECT = "direct", "Direct"
    BROKER = "broker", "Broker"
    CONTRACT = "contract", "Contract"
    FACTORY = "factory", "Factory"


class SyncStatusChoices(models.TextChoices):
    SYNCED = "synced", "Synced"
    PENDING = "pending", "Pending"
    CONFLICT = "conflict", "Conflict"


class FarmActivityTypeChoices(models.TextChoices):
    LAND_PREPARATION = "land_preparation", "Land preparation"
    PLANTING = "planting", "Planting"
    WEEDING = "weeding", "Weeding"
    FERTILIZER = "fertilizer", "Fertilizer application"
    SPRAYING = "spraying", "Spraying"
    IRRIGATION = "irrigation", "Irrigation"
    PRUNING = "pruning", "Pruning"
    HARVESTING = "harvesting", "Harvesting"
    POST_HARVEST = "post_harvest", "Post-harvest"
    OTHER = "other", "Other"


class OfflineSyncMixin(models.Model):
    client_id = models.CharField(max_length=80, blank=True, null=True, db_index=True)
    client_updated_at = models.DateTimeField(blank=True, null=True)
    sync_status = models.CharField(
        max_length=20,
        choices=SyncStatusChoices.choices,
        default=SyncStatusChoices.SYNCED,
        db_index=True,
    )
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True


class Farm(OfflineSyncMixin, BaseModel):
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farms"
    )
    farm_name = models.CharField(max_length=255)
    district = models.CharField(max_length=100)
    subcounty = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    acreage = models.DecimalField(max_digits=10, decimal_places=2)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    main_crop = models.CharField(max_length=100, blank=True, null=True)
    soil_type = models.CharField(max_length=100, blank=True, null=True)
    water_source = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["farmer", "farm_name", "district", "subcounty", "village"],
                name="unique_farm_per_farmer_location"
            )
        ]

    def clean(self):
        farm_name = (self.farm_name or "").strip()
        district = (self.district or "").strip()
        subcounty = (self.subcounty or "").strip()
        village = (self.village or "").strip()

        if not farm_name:
            raise ValidationError({"farm_name": "Farm name is required."})

        if not district:
            raise ValidationError({"district": "District is required."})

        # During ModelForm validation the farmer may be attached just before save.
        # Avoid accessing self.farmer when farmer_id is still empty because Django
        # raises RelatedObjectDoesNotExist for required relations.
        if self.farmer_id:
            duplicate_qs = Farm.objects.filter(
                farmer_id=self.farmer_id,
                farm_name__iexact=farm_name,
                district__iexact=district,
                subcounty__iexact=subcounty,
                village__iexact=village,
            )

            if self.pk:
                duplicate_qs = duplicate_qs.exclude(pk=self.pk)

            if duplicate_qs.exists():
                raise ValidationError({
                    "farm_name": "You have already recorded this farm."
                })

    def save(self, *args, **kwargs):
        self.farm_name = (self.farm_name or "").strip()
        self.district = (self.district or "").strip()
        self.subcounty = (self.subcounty or "").strip() or None
        self.village = (self.village or "").strip() or None
        self.main_crop = (self.main_crop or "").strip() or None
        self.soil_type = (self.soil_type or "").strip() or None
        self.water_source = (self.water_source or "").strip() or None

        self.full_clean()
        super().save(*args, **kwargs)


    @property
    def projects_display(self):
        names = list(self.projects.filter(is_deleted=False).values_list("name", flat=True)[:5])
        if names:
            return ", ".join(names)
        return self.main_crop or ""

    def __str__(self):
        return self.farm_name


class HarvestRecord(OfflineSyncMixin, BaseModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="harvest_records")
    project = models.ForeignKey("FarmProject", on_delete=models.SET_NULL, blank=True, null=True, related_name="harvest_records")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="harvest_records"
    )
    crop_name = models.CharField(max_length=100)
    variety = models.CharField(max_length=100, blank=True, null=True)
    season = models.CharField(max_length=100, blank=True, null=True)
    acreage_used = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    expected_yield = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    actual_yield = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    unit = models.CharField(max_length=20, default="kg")
    harvest_date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-harvest_date", "-created_at"]

    def clean(self):
        if self.project_id and self.farmer_id and self.project.farmer_id != self.farmer_id:
            raise ValidationError("The selected project does not belong to the selected farmer.")
        if self.project_id and self.farm_id and self.project.farm_id != self.farm_id:
            raise ValidationError("The selected farm must match the selected project.")
        if self.farm_id and self.farmer_id and self.farm.farmer_id != self.farmer_id:
            raise ValidationError("The selected farm does not belong to the selected farmer.")

    def save(self, *args, **kwargs):
        if self.project_id and not self.farm_id:
            self.farm = self.project.farm
        self.crop_name = (self.crop_name or "").strip()
        self.variety = (self.variety or "").strip() or None
        self.season = (self.season or "").strip() or None
        self.notes = (self.notes or "").strip() or None

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.crop_name} - {self.harvest_date}"


class FarmExpense(OfflineSyncMixin, BaseModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="expenses")
    project = models.ForeignKey("FarmProject", on_delete=models.SET_NULL, blank=True, null=True, related_name="expenses")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farm_expenses"
    )
    expense_date = models.DateField()
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    season = models.CharField(max_length=100, blank=True, null=True)
    receipt_number = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]

    def clean(self):
        if self.project_id and self.farmer_id and self.project.farmer_id != self.farmer_id:
            raise ValidationError("The selected project does not belong to the selected farmer.")
        if self.project_id and self.farm_id and self.project.farm_id != self.farm_id:
            raise ValidationError("The selected farm must match the selected project.")
        if self.farm_id and self.farmer_id and self.farm.farmer_id != self.farmer_id:
            raise ValidationError("The selected farm does not belong to the selected farmer.")

    def save(self, *args, **kwargs):
        if self.project_id and not self.farm_id:
            self.farm = self.project.farm
        self.category = (self.category or "").strip()
        self.description = (self.description or "").strip() or None
        self.season = (self.season or "").strip() or None
        self.receipt_number = (self.receipt_number or "").strip() or None

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} - {self.amount}"


class SalesRecord(OfflineSyncMixin, BaseModel):
    farm = models.ForeignKey(
        Farm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_records"
    )
    project = models.ForeignKey("FarmProject", on_delete=models.SET_NULL, blank=True, null=True, related_name="sales_records")
    harvest = models.ForeignKey(HarvestRecord, on_delete=models.SET_NULL, blank=True, null=True, related_name="sales_records")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sales_records"
    )
    crop_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20, default="kg")
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, editable=False, default=0)
    buyer_name = models.CharField(max_length=255, blank=True, null=True)
    sale_channel = models.CharField(
        max_length=20,
        choices=SaleChannelChoices.choices,
        default=SaleChannelChoices.MARKET
    )
    sale_date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-sale_date", "-created_at"]

    def clean(self):
        if self.project_id and self.farmer_id and self.project.farmer_id != self.farmer_id:
            raise ValidationError("The selected project does not belong to the selected farmer.")
        if self.project_id and self.farm_id and self.project.farm_id != self.farm_id:
            raise ValidationError("The selected farm must match the selected project.")
        if self.harvest_id and self.project_id and self.harvest.project_id and self.harvest.project_id != self.project_id:
            raise ValidationError("The sale harvest must belong to the selected project.")
        if self.farm_id and self.farmer_id and self.farm.farmer_id != self.farmer_id:
            raise ValidationError("The selected farm does not belong to the selected farmer.")

    def save(self, *args, **kwargs):
        if self.harvest_id:
            self.project = self.harvest.project or self.project
            self.farm = self.harvest.farm or self.farm
            self.crop_name = self.crop_name or self.harvest.crop_name
            self.unit = self.unit or self.harvest.unit
        if self.project_id and not self.farm_id:
            self.farm = self.project.farm
        self.crop_name = (self.crop_name or "").strip()
        self.unit = (self.unit or "").strip() or "kg"
        self.buyer_name = (self.buyer_name or "").strip() or None
        self.notes = (self.notes or "").strip() or None
        self.total_amount = (self.quantity or 0) * (self.price_per_unit or 0)

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.crop_name} - {self.sale_date}"

class FarmActivity(OfflineSyncMixin, BaseModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="activities")
    project = models.ForeignKey("FarmProject", on_delete=models.SET_NULL, blank=True, null=True, related_name="activities")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farm_activities"
    )
    activity_type = models.CharField(
        max_length=40,
        choices=FarmActivityTypeChoices.choices,
        default=FarmActivityTypeChoices.OTHER
    )
    title = models.CharField(max_length=150)
    activity_date = models.DateField()
    crop_name = models.CharField(max_length=100, blank=True, null=True)
    labour_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    input_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["farmer", "activity_date"]),
            models.Index(fields=["farmer", "updated_at"]),
        ]

    @property
    def total_cost(self):
        return (self.labour_cost or 0) + (self.input_cost or 0)

    def clean(self):
        if self.project_id and self.farmer_id and self.project.farmer_id != self.farmer_id:
            raise ValidationError("The selected project does not belong to the selected farmer.")
        if self.project_id and self.farm_id and self.project.farm_id != self.farm_id:
            raise ValidationError("The selected farm must match the selected project.")
        if self.farm_id and self.farmer_id and self.farm.farmer_id != self.farmer_id:
            raise ValidationError("The selected farm does not belong to the selected farmer.")

    def save(self, *args, **kwargs):
        if self.project_id and not self.farm_id:
            self.farm = self.project.farm
        self.title = (self.title or "").strip()
        self.crop_name = (self.crop_name or "").strip() or None
        self.notes = (self.notes or "").strip() or None
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.activity_date}"


class FarmProjectStatusChoices(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class FarmProjectTypeChoices(models.TextChoices):
    CROP = "crop", "Crop production"
    LIVESTOCK = "livestock", "Livestock"
    POULTRY = "poultry", "Poultry"
    DAIRY = "dairy", "Dairy"
    CATTLE = "cattle", "Cattle"
    GOATS = "goats", "Goats"
    PIGGERY = "piggery", "Piggery"
    FISH = "fish", "Fish farming"
    BEEKEEPING = "beekeeping", "Beekeeping / Apiary"
    HORTICULTURE = "horticulture", "Horticulture"
    FORESTRY = "forestry", "Forestry"
    OTHER = "other", "Other"


class ProjectPlanStatusChoices(models.TextChoices):
    TODO = "todo", "To do"
    IN_PROGRESS = "in_progress", "In progress"
    DONE = "done", "Done"
    MISSED = "missed", "Missed"
    CANCELLED = "cancelled", "Cancelled"


class ProjectInputCategoryChoices(models.TextChoices):
    FEEDS = "feeds", "Feeds"
    DRUGS = "drugs", "Drugs / veterinary"
    LABOUR = "labour", "Labour"
    SEED = "seed", "Seed / seedlings"
    FERTILIZER = "fertilizer", "Fertilizer"
    CHEMICALS = "chemicals", "Chemicals"
    TRANSPORT = "transport", "Transport"
    EQUIPMENT = "equipment", "Equipment"
    OTHER = "other", "Other"


class FarmProject(OfflineSyncMixin, BaseModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="projects")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farm_projects"
    )
    name = models.CharField(max_length=160)
    project_type = models.CharField(
        max_length=30,
        choices=FarmProjectTypeChoices.choices,
        default=FarmProjectTypeChoices.CROP,
        db_index=True,
    )
    acreage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    expected_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=FarmProjectStatusChoices.choices,
        default=FarmProjectStatusChoices.PLANNED,
        db_index=True,
    )
    expected_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    expected_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_unit = models.CharField(max_length=20, default="kg")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        indexes = [
            models.Index(fields=["farmer", "status"]),
            models.Index(fields=["farmer", "project_type"]),
            models.Index(fields=["farmer", "updated_at"]),
        ]

    @property
    def planned_profit(self):
        return (self.expected_revenue or 0) - (self.expected_cost or 0)

    @property
    def actual_cost(self):
        input_cost = self.input_records.filter(is_deleted=False).aggregate(total=models.Sum("total_cost"))["total"] or 0
        expense_cost = self.expenses.filter(is_deleted=False).aggregate(total=models.Sum("amount"))["total"] or 0
        activity_totals = self.activities.filter(is_deleted=False).aggregate(labour=models.Sum("labour_cost"), inputs=models.Sum("input_cost"))
        activity_cost = (activity_totals["labour"] or 0) + (activity_totals["inputs"] or 0)
        return input_cost + expense_cost + activity_cost

    @property
    def actual_revenue(self):
        project_revenue = self.revenue_records.filter(is_deleted=False).aggregate(total=models.Sum("amount"))["total"] or 0
        sales_revenue = self.sales_records.filter(is_deleted=False).aggregate(total=models.Sum("total_amount"))["total"] or 0
        return project_revenue + sales_revenue

    @property
    def estimated_profit(self):
        return (self.actual_revenue or 0) - (self.actual_cost or 0)

    @property
    def projected_profit(self):
        return (self.expected_revenue or 0) - (self.actual_cost or 0)

    @property
    def cost_variance(self):
        return (self.expected_cost or 0) - (self.actual_cost or 0)

    def clean(self):
        if self.farm_id and self.farmer_id and self.farm.farmer_id != self.farmer_id:
            raise ValidationError("The selected farm does not belong to the selected farmer.")
        if self.expected_end_date and self.start_date and self.expected_end_date < self.start_date:
            raise ValidationError({"expected_end_date": "Expected end date cannot be before the start date."})

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        self.description = (self.description or "").strip() or None
        self.target_unit = (self.target_unit or "kg").strip() or "kg"
        self.notes = (self.notes or "").strip() or None
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectPlannedActivity(OfflineSyncMixin, BaseModel):
    project = models.ForeignKey(FarmProject, on_delete=models.CASCADE, related_name="planned_activities")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="project_plans")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_planned_activities"
    )
    title = models.CharField(max_length=160)
    activity_type = models.CharField(
        max_length=40,
        choices=FarmActivityTypeChoices.choices,
        default=FarmActivityTypeChoices.OTHER,
    )
    planned_date = models.DateField()
    completed_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=ProjectPlanStatusChoices.choices,
        default=ProjectPlanStatusChoices.TODO,
        db_index=True,
    )
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    assigned_to = models.CharField(max_length=120, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["planned_date", "created_at"]
        indexes = [
            models.Index(fields=["farmer", "planned_date"]),
            models.Index(fields=["project", "status"]),
        ]

    @property
    def cost_variance(self):
        return (self.estimated_cost or 0) - (self.actual_cost or 0)

    def clean(self):
        if self.project_id and self.farmer_id and self.project.farmer_id != self.farmer_id:
            raise ValidationError("The selected project does not belong to the selected farmer.")
        if self.farm_id and self.project_id and self.farm_id != self.project.farm_id:
            raise ValidationError("The selected farm must match the project farm.")

    def save(self, *args, **kwargs):
        if self.project_id and not self.farm_id:
            self.farm = self.project.farm
        self.title = (self.title or "").strip()
        self.assigned_to = (self.assigned_to or "").strip() or None
        self.notes = (self.notes or "").strip() or None
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.planned_date}"


class ProjectInputRecord(OfflineSyncMixin, BaseModel):
    project = models.ForeignKey(FarmProject, on_delete=models.CASCADE, related_name="input_records")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="project_inputs")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_input_records"
    )
    category = models.CharField(
        max_length=30,
        choices=ProjectInputCategoryChoices.choices,
        default=ProjectInputCategoryChoices.OTHER,
        db_index=True,
    )
    item_name = models.CharField(max_length=160)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, default="unit")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, editable=False, default=0)
    record_date = models.DateField(db_index=True)
    supplier_name = models.CharField(max_length=160, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-record_date", "-created_at"]
        indexes = [
            models.Index(fields=["farmer", "category"]),
            models.Index(fields=["project", "record_date"]),
        ]

    def clean(self):
        if self.project_id and self.farmer_id and self.project.farmer_id != self.farmer_id:
            raise ValidationError("The selected project does not belong to the selected farmer.")
        if self.farm_id and self.project_id and self.farm_id != self.project.farm_id:
            raise ValidationError("The selected farm must match the project farm.")

    def save(self, *args, **kwargs):
        if self.project_id and not self.farm_id:
            self.farm = self.project.farm
        self.item_name = (self.item_name or "").strip()
        self.unit = (self.unit or "unit").strip() or "unit"
        self.supplier_name = (self.supplier_name or "").strip() or None
        self.notes = (self.notes or "").strip() or None
        self.total_cost = (self.quantity or 0) * (self.unit_cost or 0)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} - {self.total_cost}"


class ProjectRevenueRecord(OfflineSyncMixin, BaseModel):
    project = models.ForeignKey(FarmProject, on_delete=models.CASCADE, related_name="revenue_records")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="project_revenues")
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_revenue_records"
    )
    description = models.CharField(max_length=180)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default="unit")
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2, editable=False, default=0)
    revenue_date = models.DateField(db_index=True)
    buyer_name = models.CharField(max_length=160, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-revenue_date", "-created_at"]
        indexes = [models.Index(fields=["project", "revenue_date"])]

    def clean(self):
        if self.project_id and self.farmer_id and self.project.farmer_id != self.farmer_id:
            raise ValidationError("The selected project does not belong to the selected farmer.")
        if self.farm_id and self.project_id and self.farm_id != self.project.farm_id:
            raise ValidationError("The selected farm must match the project farm.")

    def save(self, *args, **kwargs):
        if self.project_id and not self.farm_id:
            self.farm = self.project.farm
        self.description = (self.description or "").strip()
        self.unit = (self.unit or "unit").strip() or "unit"
        self.buyer_name = (self.buyer_name or "").strip() or None
        self.notes = (self.notes or "").strip() or None
        self.amount = (self.quantity or 0) * (self.price_per_unit or 0)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - {self.amount}"
