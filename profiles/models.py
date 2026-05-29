from django.conf import settings
from django.db import models
from core.models import BaseModel


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class BusinessApprovalStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class BusinessDocumentTypeChoices(models.TextChoices):
    CERTIFICATE_OF_REGISTRATION = "certificate_of_registration", "Certificate of Registration"
    TRADING_LICENSE = "trading_license", "Trading License"
    TIN_CERTIFICATE = "tin_certificate", "TIN Certificate"
    NATIONAL_ID = "national_id", "National ID"
    OTHER = "other", "Other"


class FarmerProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farmer_profile"
    )
    national_id = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GenderChoices.choices, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    subcounty = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    primary_crop = models.CharField(max_length=100, blank=True, null=True)
    farming_experience_years = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Farmer Profile - {self.user.full_name}"


class BusinessProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_profile"
    )
    business_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    tin_number = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    physical_address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    approval_status = models.CharField(
        max_length=20,
        choices=BusinessApprovalStatusChoices.choices,
        default=BusinessApprovalStatusChoices.PENDING
    )
    submitted_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.business_name


class BusinessVerificationDocument(BaseModel):
    business_profile = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    document_type = models.CharField(max_length=50, choices=BusinessDocumentTypeChoices.choices)
    file = models.FileField(upload_to="business_verification_documents/")
    review_note = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_profile.business_name} - {self.document_type}"