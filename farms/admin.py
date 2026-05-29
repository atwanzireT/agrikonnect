from django.contrib import admin

from .models import (
    Farm, HarvestRecord, FarmExpense, SalesRecord, FarmActivity,
    FarmProject, ProjectPlannedActivity, ProjectInputRecord, ProjectRevenueRecord,
)


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = (
        "farm_name",
        "farmer",
        "district",
        "subcounty",
        "village",
        "acreage",
        "main_crop",
        "created_at",
    )
    list_filter = ("district", "main_crop", "created_at")
    search_fields = (
        "farm_name",
        "farmer__full_name",
        "farmer__phone",
        "farmer__email",
        "district",
        "subcounty",
        "village",
        "main_crop",
    )
    autocomplete_fields = ("farmer",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(HarvestRecord)
class HarvestRecordAdmin(admin.ModelAdmin):
    list_display = (
        "crop_name",
        "farm",
        "farmer",
        "season",
        "expected_yield",
        "actual_yield",
        "unit",
        "harvest_date",
        "created_at",
    )
    list_filter = ("crop_name", "season", "unit", "harvest_date", "created_at")
    search_fields = (
        "crop_name",
        "variety",
        "season",
        "farm__farm_name",
        "farmer__full_name",
        "farmer__phone",
    )
    autocomplete_fields = ("farm", "farmer")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-harvest_date", "-created_at")


@admin.register(FarmExpense)
class FarmExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "category",
        "farm",
        "farmer",
        "amount",
        "season",
        "receipt_number",
        "expense_date",
        "created_at",
    )
    list_filter = ("category", "season", "expense_date", "created_at")
    search_fields = (
        "category",
        "description",
        "farm__farm_name",
        "farmer__full_name",
        "receipt_number",
    )
    autocomplete_fields = ("farm", "farmer")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-expense_date", "-created_at")


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = (
        "crop_name",
        "farm",
        "farmer",
        "quantity",
        "unit",
        "price_per_unit",
        "total_amount",
        "buyer_name",
        "sale_channel",
        "sale_date",
    )
    list_filter = ("crop_name", "sale_channel", "sale_date", "created_at")
    search_fields = (
        "crop_name",
        "buyer_name",
        "farm__farm_name",
        "farmer__full_name",
        "farmer__phone",
    )
    autocomplete_fields = ("farm", "farmer")
    readonly_fields = ("id", "total_amount", "created_at", "updated_at")
    ordering = ("-sale_date", "-created_at")

@admin.register(FarmActivity)
class FarmActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "activity_type", "farm", "farmer", "activity_date", "labour_cost", "input_cost", "created_at")
    list_filter = ("activity_type", "activity_date", "created_at")
    search_fields = ("title", "crop_name", "notes", "farm__farm_name", "farmer__full_name", "farmer__phone")
    autocomplete_fields = ("farm", "farmer")
    readonly_fields = ("id", "total_cost", "created_at", "updated_at")
    ordering = ("-activity_date", "-created_at")


@admin.register(FarmProject)
class FarmProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "project_type", "farm", "farmer", "status", "start_date", "expected_revenue", "expected_cost", "planned_profit")
    list_filter = ("project_type", "status", "start_date", "created_at")
    search_fields = ("name", "description", "farm__farm_name", "farmer__full_name", "farmer__phone")
    autocomplete_fields = ("farm", "farmer")
    readonly_fields = ("id", "planned_profit", "actual_cost", "actual_revenue", "estimated_profit", "projected_profit", "cost_variance", "created_at", "updated_at")
    ordering = ("-start_date", "-created_at")


@admin.register(ProjectPlannedActivity)
class ProjectPlannedActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "farmer", "planned_date", "status", "estimated_cost", "actual_cost", "cost_variance")
    list_filter = ("status", "activity_type", "planned_date", "created_at")
    search_fields = ("title", "project__name", "farm__farm_name", "farmer__full_name", "assigned_to")
    autocomplete_fields = ("project", "farm", "farmer")
    readonly_fields = ("id", "cost_variance", "created_at", "updated_at")
    ordering = ("planned_date", "created_at")


@admin.register(ProjectInputRecord)
class ProjectInputRecordAdmin(admin.ModelAdmin):
    list_display = ("item_name", "category", "project", "farmer", "quantity", "unit_cost", "total_cost", "record_date")
    list_filter = ("category", "record_date", "created_at")
    search_fields = ("item_name", "supplier_name", "project__name", "farm__farm_name", "farmer__full_name")
    autocomplete_fields = ("project", "farm", "farmer")
    readonly_fields = ("id", "total_cost", "created_at", "updated_at")
    ordering = ("-record_date", "-created_at")


@admin.register(ProjectRevenueRecord)
class ProjectRevenueRecordAdmin(admin.ModelAdmin):
    list_display = ("description", "project", "farmer", "quantity", "price_per_unit", "amount", "buyer_name", "revenue_date")
    list_filter = ("revenue_date", "created_at")
    search_fields = ("description", "buyer_name", "project__name", "farm__farm_name", "farmer__full_name")
    autocomplete_fields = ("project", "farm", "farmer")
    readonly_fields = ("id", "amount", "created_at", "updated_at")
    ordering = ("-revenue_date", "-created_at")
