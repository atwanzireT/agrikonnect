from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User, PhoneOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "full_name",
        "email",
        "phone",
        "account_type",
        "district",
        "is_phone_verified",
        "is_email_verified",
        "is_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = (
        "account_type",
        "is_phone_verified",
        "is_email_verified",
        "is_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )
    search_fields = ("full_name", "email", "phone", "district")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "updated_at", "last_login")
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        ("Login Credentials", {
            "fields": ("email", "phone", "password")
        }),
        ("Personal Information", {
            "fields": ("id", "full_name", "district", "account_type")
        }),
        ("Verification Status", {
            "fields": ("is_phone_verified", "is_email_verified", "is_verified")
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined", "updated_at")
        }),
    )

    add_fieldsets = (
        ("Create User", {
            "classes": ("wide",),
            "fields": (
                "full_name",
                "email",
                "phone",
                "district",
                "account_type",
                "password1",
                "password2",
                "is_active",
                "is_staff",
                "is_verified",
            ),
        }),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "purpose",
        "attempts",
        "expires_at",
        "consumed_at",
        "created_at",
        "otp_status",
    )
    list_filter = ("purpose", "created_at", "expires_at", "consumed_at")
    search_fields = ("phone",)
    readonly_fields = ("id", "code_hash", "created_at")
    ordering = ("-created_at",)

    def otp_status(self, obj):
        if obj.consumed_at:
            return format_html('<span style="color: green; font-weight: 600;">Consumed</span>')
        if obj.is_expired():
            return format_html('<span style="color: red; font-weight: 600;">Expired</span>')
        return format_html('<span style="color: #d97706; font-weight: 600;">Active</span>')

    otp_status.short_description = "Status"