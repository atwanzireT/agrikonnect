import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class AccountTypeChoices(models.TextChoices):
    FARMER = "farmer", "Farmer"
    BUSINESS = "business", "Business"
    ADMIN = "admin", "Admin"


class PhoneOTPPurposeChoices(models.TextChoices):
    SIGNUP = "signup", "Signup"
    PASSWORD_RESET = "password_reset", "Password Reset"
    PHONE_CHANGE = "phone_change", "Phone Change"


class UserManager(BaseUserManager):
    def create_user(
        self,
        full_name,
        password=None,
        phone=None,
        email=None,
        account_type=AccountTypeChoices.FARMER,
        **extra_fields
    ):
        if not phone and not email:
            raise ValueError("A user must have either a phone number or an email address.")

        email = self.normalize_email(email) if email else None

        user = self.model(
            full_name=full_name,
            phone=phone,
            email=email,
            account_type=account_type,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, full_name, password, email, phone=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_email_verified", True)
        extra_fields.setdefault("account_type", AccountTypeChoices.ADMIN)

        if not email:
            raise ValueError("Superuser must have an email address.")

        return self.create_user(
            full_name=full_name,
            password=password,
            email=email,
            phone=phone,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    account_type = models.CharField(max_length=20, choices=AccountTypeChoices.choices)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.full_name or self.email or self.phone or str(self.id)


class PhoneOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, db_index=True)
    code_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=30, choices=PhoneOTPPurposeChoices.choices)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_consumed(self):
        return self.consumed_at is not None

    def __str__(self):
        return f"{self.phone} - {self.purpose}"