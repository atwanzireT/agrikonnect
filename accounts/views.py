import hashlib
import logging
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
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
from .utils import send_sms, normalize_ugandan_phone
from profiles.models import FarmerProfile, BusinessProfile

logger = logging.getLogger(__name__)

AUTH_BACKEND = "accounts.backends.EmailOrPhoneBackend"


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def safe_login(request, user):
    login(request, user, backend=AUTH_BACKEND)


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect("core:home")

    if request.user.account_type == AccountTypeChoices.FARMER:
        return redirect("farms:farmer_dashboard")

    if request.user.account_type == AccountTypeChoices.BUSINESS:
        return redirect("marketplace:business_dashboard")

    return redirect("/admin/")


@require_http_methods(["GET", "POST"])
def farmer_request_otp(request):
    form = FarmerPhoneForm(request.POST or None)

    if request.method == "POST":
        try:
            if form.is_valid():
                phone = normalize_ugandan_phone(form.cleaned_data["phone"])
                code = generate_otp()

                otp = PhoneOTP.objects.create(
                    phone=phone,
                    code_hash=hash_code(code),
                    purpose=PhoneOTPPurposeChoices.SIGNUP,
                    expires_at=timezone.now() + timedelta(minutes=5),
                )

                sms_sent, sms_response = send_sms(
                    phone,
                    f"Your AgriKonnect OTP code is {code}. It expires in 5 minutes.",
                )

                if not sms_sent:
                    otp.delete()
                    messages.error(request, f"Failed to send OTP SMS. {sms_response}")
                    return render(request, "accounts/farmer_request_otp.html", {"form": form})

                request.session["verified_signup_phone"] = phone
                messages.success(request, "OTP sent successfully.")
                return redirect("accounts:farmer_verify_otp")

        except Exception as exc:
            logger.exception("Farmer OTP request failed")
            messages.error(request, f"Server error: {str(exc)}")

    return render(request, "accounts/farmer_request_otp.html", {"form": form})


@require_http_methods(["GET", "POST"])
def farmer_verify_otp(request):
    phone = request.session.get("verified_signup_phone", "")
    form = OTPVerificationForm(request.POST or None, initial={"phone": phone})

    if request.method == "POST" and form.is_valid():
        phone = form.cleaned_data["phone"]
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
            messages.error(request, "No active OTP found.")
        elif otp.is_expired():
            messages.error(request, "OTP has expired.")
        elif otp.attempts >= 5:
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

            messages.success(request, "Phone verified successfully.")
            return redirect("accounts:farmer_signup")

    return render(request, "accounts/farmer_verify_otp.html", {"form": form, "phone": phone})


@require_http_methods(["GET", "POST"])
def farmer_signup(request):
    if not request.session.get("phone_otp_verified"):
        messages.error(request, "Please verify your phone first.")
        return redirect("accounts:farmer_request_otp")

    verified_phone = request.session.get("verified_phone")
    form = FarmerSignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        if User.objects.filter(phone=verified_phone).exists():
            messages.error(request, "An account with this phone number already exists.")
            return render(
                request,
                "accounts/farmer_signup.html",
                {"form": form, "verified_phone": verified_phone},
            )

        user = User.objects.create_user(
            full_name=form.cleaned_data["full_name"],
            password=form.cleaned_data["password"],
            phone=verified_phone,
            district=form.cleaned_data.get("district"),
            account_type=AccountTypeChoices.FARMER,
            is_phone_verified=True,
            is_verified=True,
        )

        FarmerProfile.objects.create(
            user=user,
            district=form.cleaned_data.get("district"),
        )

        request.session.pop("phone_otp_verified", None)
        request.session.pop("verified_phone", None)
        request.session.pop("verified_signup_phone", None)

        safe_login(request, user)
        messages.success(request, "Farmer account created successfully.")
        return redirect("farms:farmer_dashboard")

    return render(
        request,
        "accounts/farmer_signup.html",
        {"form": form, "verified_phone": verified_phone},
    )


@require_http_methods(["GET", "POST"])
def farmer_login(request):
    form = FarmerLoginForm(request.POST or None, request=request)

    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        safe_login(request, user)
        return redirect("farms:farmer_dashboard")

    return render(request, "accounts/farmer_login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def business_signup(request):
    form = BusinessSignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
            district=form.cleaned_data.get("district"),
            account_type=AccountTypeChoices.BUSINESS,
            is_email_verified=True,
            is_verified=True,
        )

        BusinessProfile.objects.create(
            user=user,
            business_name=form.cleaned_data["full_name"],
            contact_person=form.cleaned_data["full_name"],
            district=form.cleaned_data.get("district"),
        )

        safe_login(request, user)
        messages.success(request, "Business account created successfully.")
        return redirect("marketplace:business_dashboard")

    return render(request, "accounts/business_signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def business_login(request):
    form = BusinessLoginForm(request.POST or None, request=request)

    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        safe_login(request, user)
        return redirect("marketplace:business_dashboard")

    return render(request, "accounts/business_login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("core:home")