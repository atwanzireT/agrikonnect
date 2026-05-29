from django.contrib import admin

from .models import (
    FarmerProfile,
    BusinessProfile,
    BusinessVerificationDocument,
)


class BusinessVerificationDocumentInline(admin.TabularInline):
    model = BusinessVerificationDocument
    extra = 1
    fields = ("document_type", "file", "review_note", "is_active", "created_at")
    readonly_fields = ("created_at",)


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "national_id",
        "gender",
        "district",
        "subcounty",
        "village",
        "primary_crop",
        "farming_experience_years",
        "created_at",
    )
    list_filter = ("gender", "district", "primary_crop", "created_at")
    search_fields = (
        "user__full_name",
        "user__phone",
        "user__email",
        "national_id",
        "district",
        "subcounty",
        "village",
        "primary_crop",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "user",
        "contact_person",
        "business_type",
        "district",
        "approval_status",
        "submitted_at",
        "verified_at",
        "created_at",
    )
    list_filter = (
        "approval_status",
        "business_type",
        "district",
        "submitted_at",
        "verified_at",
        "created_at",
    )
    search_fields = (
        "business_name",
        "user__full_name",
        "user__email",
        "user__phone",
        "contact_person",
        "registration_number",
        "tin_number",
        "district",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [BusinessVerificationDocumentInline]

    actions = ["mark_approved", "mark_rejected", "mark_pending"]

    @admin.action(description="Mark selected businesses as approved")
    def mark_approved(self, request, queryset):
        queryset.update(approval_status="approved")

    @admin.action(description="Mark selected businesses as rejected")
    def mark_rejected(self, request, queryset):
        queryset.update(approval_status="rejected")

    @admin.action(description="Mark selected businesses as pending")
    def mark_pending(self, request, queryset):
        queryset.update(approval_status="pending")


@admin.register(BusinessVerificationDocument)
class BusinessVerificationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "business_profile",
        "document_type",
        "is_active",
        "created_at",
    )
    list_filter = ("document_type", "is_active", "created_at")
    search_fields = (
        "business_profile__business_name",
        "business_profile__user__full_name",
        "business_profile__user__email",
    )
    autocomplete_fields = ("business_profile",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)