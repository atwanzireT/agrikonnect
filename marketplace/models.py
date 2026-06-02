from django.conf import settings
from django.db import models
from core.models import BaseModel
from farms.models import Farm


class ListingStatusChoices(models.TextChoices):
    DRAFT = "draft", "Draft"
    OPEN = "open", "Open"
    RESERVED = "reserved", "Reserved"
    SOLD = "sold", "Sold"
    CLOSED = "closed", "Closed"


class RequestStatusChoices(models.TextChoices):
    OPEN = "open", "Open"
    MATCHED = "matched", "Matched"
    CLOSED = "closed", "Closed"
    CANCELLED = "cancelled", "Cancelled"


class InquiryStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    CONTACTED = "contacted", "Contacted"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    CLOSED = "closed", "Closed"


class ProduceListing(BaseModel):
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="produce_listings"
    )
    farm = models.ForeignKey(
        Farm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produce_listings"
    )
    crop_name = models.CharField(max_length=100)
    variety = models.CharField(max_length=100, blank=True, null=True)
    quality = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20, default="kg")
    expected_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    district = models.CharField(max_length=100)
    subcounty = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    available_from = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=ListingStatusChoices.choices,
        default=ListingStatusChoices.DRAFT
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.crop_name} - {self.quantity} {self.unit}"


class ProduceListingImage(BaseModel):
    listing = models.ForeignKey(
        ProduceListing,
        on_delete=models.CASCADE,
        related_name="images"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="produce_listing_images"
    )
    image = models.ImageField(upload_to="produce_listing_images/")
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"Image for {self.listing}"


class ListingInquiry(BaseModel):
    listing = models.ForeignKey(
        ProduceListing,
        on_delete=models.CASCADE,
        related_name="inquiries"
    )
    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listing_inquiries"
    )
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=InquiryStatusChoices.choices,
        default=InquiryStatusChoices.PENDING
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inquiry on {self.listing}"


class BuyerRequest(BaseModel):
    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_requests"
    )
    crop_name = models.CharField(max_length=100)
    variety = models.CharField(max_length=100, blank=True, null=True)
    quantity_needed = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20, default="kg")
    min_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    delivery_district = models.CharField(max_length=100, blank=True, null=True)
    delivery_location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    date_needed = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.OPEN
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.crop_name} request - {self.quantity_needed} {self.unit}"


class BuyerRequestImage(BaseModel):
    buyer_request = models.ForeignKey(
        BuyerRequest,
        on_delete=models.CASCADE,
        related_name="images"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_request_images"
    )
    image = models.ImageField(upload_to="buyer_request_images/")
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"Image for {self.buyer_request}"

class PurchaseStatusChoices(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class MarketplacePurchase(BaseModel):
    listing = models.ForeignKey(
        ProduceListing,
        on_delete=models.CASCADE,
        related_name="purchases"
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketplace_purchases"
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    delivery_location = models.CharField(max_length=255, blank=True, null=True)
    buyer_phone = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=PurchaseStatusChoices.choices, default=PurchaseStatusChoices.PENDING)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.unit_price is None:
            self.unit_price = self.listing.expected_price
        if self.unit_price is not None and self.quantity is not None:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Purchase request for {self.listing} by {self.buyer}"
