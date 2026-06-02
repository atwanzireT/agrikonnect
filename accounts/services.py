from django.db import transaction

from .models import User, AccountTypeChoices
from .utils import normalize_ugandan_phone
from profiles.models import FarmerProfile, BusinessProfile


def normalize_registration_phone(phone):
    """Normalize Ugandan phone numbers consistently for web and mobile registration."""
    if not phone:
        return None
    return normalize_ugandan_phone(phone)


@transaction.atomic
def create_farmer_account(*, full_name, password, phone=None, email=None, district=None, verified=False):
    """Create a farmer User and FarmerProfile from either the web portal or mobile API."""
    phone = normalize_registration_phone(phone)
    email = (email or None)
    if email:
        email = email.strip().lower()

    if not phone and not email:
        raise ValueError("A farmer account needs either a phone number or an email address.")

    user = User.objects.create_user(
        full_name=full_name,
        password=password,
        phone=phone,
        email=email,
        district=district,
        account_type=AccountTypeChoices.FARMER,
        is_verified=verified,
        is_phone_verified=bool(phone) and verified,
        is_email_verified=bool(email) and verified,
    )

    FarmerProfile.objects.get_or_create(
        user=user,
        defaults={"district": district},
    )
    return user


@transaction.atomic
def create_business_account(*, full_name, password, email, district=None, verified=True):
    """Create a business User and BusinessProfile using one shared code path."""
    email = email.strip().lower()
    user = User.objects.create_user(
        full_name=full_name,
        email=email,
        password=password,
        district=district,
        account_type=AccountTypeChoices.BUSINESS,
        is_email_verified=verified,
        is_verified=verified,
    )

    BusinessProfile.objects.get_or_create(
        user=user,
        defaults={
            "business_name": full_name,
            "contact_person": full_name,
            "district": district,
        },
    )
    return user
