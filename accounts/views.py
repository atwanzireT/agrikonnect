import hashlib
import logging
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import (
    FarmerPhoneForm,
    OTPVerificationForm,
    FarmerSignupForm,
    FarmerLoginForm,
    BusinessSignupForm,
    BusinessLoginForm,
)
from .models import PhoneOTP, User, AccountTypeChoices, PhoneOTPPurposeChoices
from .services import create_farmer_account, create_business_account
from .utils import send_sms, normalize_ugandan_phone

logger = logging.getLogger(__name__)

AUTH_BACKEND = "accounts.backends.EmailOrPhoneBackend"
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def safe_login(request, user):
    login(request, user, backend=AUTH_BACKEND)


def hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()


def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect("core:home")

    if request.user.account_type in [AccountTypeChoices.FARMER, AccountTypeChoices.GUEST]:
        return redirect("marketplace:listing_list")

    if request.user.account_type == AccountTypeChoices.BUSINESS:
        return redirect("marketplace:listing_list")

    return redirect("/admin/")


@require_http_methods(["GET", "POST"])
def farmer_request_otp(request):
    form = FarmerPhoneForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            phone = normalize_ugandan_phone(form.cleaned_data["phone"])

            if User.objects.filter(phone=phone).exists():
                messages.error(request, "An account with this phone number already exists.")
                return render(request, "accounts/farmer_request_otp.html", {"form": form})

            PhoneOTP.objects.filter(
                phone=phone,
                purpose=PhoneOTPPurposeChoices.SIGNUP,
                consumed_at__isnull=True,
            ).update(consumed_at=timezone.now())

            code = generate_otp()
            otp = PhoneOTP.objects.create(
                phone=phone,
                code_hash=hash_code(code),
                purpose=PhoneOTPPurposeChoices.SIGNUP,
                expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            )

            sms_sent, sms_response = send_sms(
                phone,
                f"Your AgroSync OTP code is {code}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
            )

            if not sms_sent:
                otp.delete()
                messages.error(request, f"Failed to send OTP SMS. {sms_response}")
                return render(request, "accounts/farmer_request_otp.html", {"form": form})

            request.session["verified_signup_phone"] = phone
            request.session.pop("phone_otp_verified", None)
            request.session.pop("verified_phone", None)
            request.session.modified = True

            messages.success(request, "OTP sent successfully. Please enter the code sent to your phone.")
            return redirect("accounts:farmer_verify_otp")

        except Exception as exc:
            logger.exception("Farmer OTP request failed")
            messages.error(request, f"Server error: {str(exc)}")

    return render(request, "accounts/farmer_request_otp.html", {"form": form})


@require_http_methods(["GET", "POST"])
def farmer_verify_otp(request):
    session_phone = request.session.get("verified_signup_phone")

    if not session_phone:
        messages.error(request, "Please enter your phone number first.")
        return redirect("accounts:farmer_request_otp")

    phone = normalize_ugandan_phone(session_phone)
    form = OTPVerificationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]

        otp = (
            PhoneOTP.objects.filter(
                phone=phone,
                purpose=PhoneOTPPurposeChoices.SIGNUP,
                consumed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp:
            messages.error(request, "No active OTP found. Please request a new OTP.")
        elif otp.is_expired():
            otp.consumed_at = timezone.now()
            otp.save(update_fields=["consumed_at"])
            messages.error(request, "OTP has expired. Please request a new OTP.")
        elif otp.attempts >= MAX_OTP_ATTEMPTS:
            messages.error(request, "Too many failed attempts. Please request a new OTP.")
        elif otp.code_hash != hash_code(code):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            messages.error(request, "Invalid OTP code.")
        else:
            otp.consumed_at = timezone.now()
            otp.save(update_fields=["consumed_at"])

            request.session["phone_otp_verified"] = True
            request.session["verified_phone"] = phone
            request.session.modified = True

            messages.success(request, "Phone verified successfully. Complete your farmer account.")
            return redirect("accounts:farmer_signup")

    return render(request, "accounts/farmer_verify_otp.html", {"form": form, "phone": phone})


@require_http_methods(["POST"])
def farmer_resend_otp(request):
    session_phone = request.session.get("verified_signup_phone")

    if not session_phone:
        messages.error(request, "Please enter your phone number again.")
        return redirect("accounts:farmer_request_otp")

    try:
        phone = normalize_ugandan_phone(session_phone)

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "An account with this phone number already exists.")
            return redirect("accounts:farmer_request_otp")

        PhoneOTP.objects.filter(
            phone=phone,
            purpose=PhoneOTPPurposeChoices.SIGNUP,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())

        code = generate_otp()
        otp = PhoneOTP.objects.create(
            phone=phone,
            code_hash=hash_code(code),
            purpose=PhoneOTPPurposeChoices.SIGNUP,
            expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        )

        sms_sent, sms_response = send_sms(
            phone,
            f"Your AgroSync OTP code is {code}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
        )

        if not sms_sent:
            otp.delete()
            messages.error(request, f"Failed to resend OTP SMS. {sms_response}")
        else:
            messages.success(request, "A new OTP has been sent. Use the latest code only.")

    except Exception as exc:
        logger.exception("Farmer OTP resend failed")
        messages.error(request, f"Server error: {str(exc)}")

    return redirect("accounts:farmer_verify_otp")


@require_http_methods(["GET", "POST"])
def farmer_signup(request):
    if not request.session.get("phone_otp_verified"):
        messages.error(request, "Please verify your phone first.")
        return redirect("accounts:farmer_request_otp")

    verified_phone = normalize_ugandan_phone(request.session.get("verified_phone"))

    if not verified_phone:
        messages.error(request, "Your verification session expired. Please verify your phone again.")
        return redirect("accounts:farmer_request_otp")

    form = FarmerSignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        if User.objects.filter(phone=verified_phone).exists():
            messages.error(request, "An account with this phone number already exists.")
            return render(request, "accounts/farmer_signup.html", {"form": form, "verified_phone": verified_phone})

        user = create_farmer_account(
            full_name=form.cleaned_data["full_name"],
            password=form.cleaned_data["password"],
            phone=verified_phone,
            district=form.cleaned_data.get("district"),
            verified=True,
        )

        request.session.pop("phone_otp_verified", None)
        request.session.pop("verified_phone", None)
        request.session.pop("verified_signup_phone", None)
        request.session.modified = True

        safe_login(request, user)
        messages.success(request, "Farmer account created successfully.")
        return redirect("marketplace:listing_list")

    return render(request, "accounts/farmer_signup.html", {"form": form, "verified_phone": verified_phone})


@require_http_methods(["GET", "POST"])
def farmer_login(request):
    form = FarmerLoginForm(request.POST or None, request=request)

    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        safe_login(request, user)
        return redirect("marketplace:listing_list")

    return render(request, "accounts/farmer_login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def business_signup(request):
    form = BusinessSignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = create_business_account(
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
            district=form.cleaned_data.get("district"),
            verified=True,
        )

        safe_login(request, user)
        messages.success(request, "Business account created successfully.")
        return redirect("marketplace:listing_list")

    return render(request, "accounts/business_signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def business_login(request):
    form = BusinessLoginForm(request.POST or None, request=request)

    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        safe_login(request, user)
        return redirect("marketplace:listing_list")

    return render(request, "accounts/business_login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("core:home")
