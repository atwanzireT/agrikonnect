import hashlib
import logging
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
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


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def form_errors(form):
    return {
        field: [str(error) for error in errors]
        for field, errors in form.errors.items()
    }


def json_success(redirect_url=None, message=None, extra=None):
    data = {"success": True}
    if redirect_url:
        data["redirect_url"] = redirect_url
    if message:
        data["message"] = message
    if extra:
        data.update(extra)
    return JsonResponse(data)


def json_error(message, errors=None, status=400):
    data = {
        "success": False,
        "message": message,
    }
    if errors:
        data["errors"] = errors
    return JsonResponse(data, status=status)


def safe_login(request, user):
    login(request, user, backend=AUTH_BACKEND)


def hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()


def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect("core:home")

    if request.user.account_type in [
        AccountTypeChoices.FARMER,
        AccountTypeChoices.GUEST,
        AccountTypeChoices.BUSINESS,
    ]:
        return redirect("marketplace:listing_list")

    return redirect("/admin/")


@require_http_methods(["GET", "POST"])
def farmer_request_otp(request):
    form = FarmerPhoneForm(request.POST or None)

    if request.method == "POST":
        if not form.is_valid():
            if is_ajax(request):
                return json_error(
                    "Please enter a valid phone number.",
                    errors=form_errors(form),
                )
            return render(request, "accounts/farmer_request_otp.html", {"form": form})

        try:
            phone = normalize_ugandan_phone(form.cleaned_data["phone"])

            if User.objects.filter(phone=phone).exists():
                message = "An account with this phone number already exists."
                if is_ajax(request):
                    return json_error(message)
                messages.error(request, message)
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
                message = f"Failed to send OTP SMS. {sms_response}"
                if is_ajax(request):
                    return json_error(message, status=502)
                messages.error(request, message)
                return render(request, "accounts/farmer_request_otp.html", {"form": form})

            request.session["verified_signup_phone"] = phone
            request.session.pop("phone_otp_verified", None)
            request.session.pop("verified_phone", None)
            request.session.modified = True

            redirect_url = reverse("accounts:farmer_verify_otp")
            message = "OTP sent successfully. Please enter the code sent to your phone."

            if is_ajax(request):
                return json_success(redirect_url=redirect_url, message=message)

            messages.success(request, message)
            return redirect("accounts:farmer_verify_otp")

        except Exception as exc:
            logger.exception("Farmer OTP request failed")
            message = f"Server error: {str(exc)}"
            if is_ajax(request):
                return json_error(message, status=500)
            messages.error(request, message)

    return render(request, "accounts/farmer_request_otp.html", {"form": form})


@require_http_methods(["GET", "POST"])
def farmer_verify_otp(request):
    session_phone = request.session.get("verified_signup_phone")

    if not session_phone:
        message = "Please enter your phone number first."
        if is_ajax(request):
            return json_error(
                message,
                extra={"redirect_url": reverse("accounts:farmer_request_otp")},
            )
        messages.error(request, message)
        return redirect("accounts:farmer_request_otp")

    phone = normalize_ugandan_phone(session_phone)
    form = OTPVerificationForm(request.POST or None)

    if request.method == "POST":
        if not form.is_valid():
            if is_ajax(request):
                return json_error(
                    "Enter a valid 6-digit OTP code.",
                    errors=form_errors(form),
                )
            return render(request, "accounts/farmer_verify_otp.html", {"form": form, "phone": phone})

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
            message = "No active OTP found. Please request a new OTP."
            if is_ajax(request):
                return json_error(message)
            messages.error(request, message)

        elif otp.is_expired():
            otp.consumed_at = timezone.now()
            otp.save(update_fields=["consumed_at"])

            message = "OTP has expired. Please request a new OTP."
            if is_ajax(request):
                return json_error(message)
            messages.error(request, message)

        elif otp.attempts >= MAX_OTP_ATTEMPTS:
            message = "Too many failed attempts. Please request a new OTP."
            if is_ajax(request):
                return json_error(message)
            messages.error(request, message)

        elif otp.code_hash != hash_code(code):
            otp.attempts += 1
            otp.save(update_fields=["attempts"])

            message = "Invalid OTP code."
            if is_ajax(request):
                return json_error(message)
            messages.error(request, message)

        else:
            otp.consumed_at = timezone.now()
            otp.save(update_fields=["consumed_at"])

            request.session["phone_otp_verified"] = True
            request.session["verified_phone"] = phone
            request.session.modified = True

            redirect_url = reverse("accounts:farmer_signup")
            message = "Phone verified successfully. Complete your farmer account."

            if is_ajax(request):
                return json_success(redirect_url=redirect_url, message=message)

            messages.success(request, message)
            return redirect("accounts:farmer_signup")

    return render(request, "accounts/farmer_verify_otp.html", {"form": form, "phone": phone})


@require_http_methods(["POST"])
def farmer_resend_otp(request):
    session_phone = request.session.get("verified_signup_phone")

    if not session_phone:
        message = "Please enter your phone number again."
        redirect_url = reverse("accounts:farmer_request_otp")

        if is_ajax(request):
            return json_error(message, status=400)

        messages.error(request, message)
        return redirect(redirect_url)

    try:
        phone = normalize_ugandan_phone(session_phone)

        if User.objects.filter(phone=phone).exists():
            message = "An account with this phone number already exists."
            if is_ajax(request):
                return json_error(message)
            messages.error(request, message)
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
            message = f"Failed to resend OTP SMS. {sms_response}"
            if is_ajax(request):
                return json_error(message, status=502)
            messages.error(request, message)
        else:
            message = "A new OTP has been sent. Use the latest code only."
            if is_ajax(request):
                return json_success(
                    redirect_url=reverse("accounts:farmer_verify_otp"),
                    message=message,
                )
            messages.success(request, message)

    except Exception as exc:
        logger.exception("Farmer OTP resend failed")
        message = f"Server error: {str(exc)}"
        if is_ajax(request):
            return json_error(message, status=500)
        messages.error(request, message)

    return redirect("accounts:farmer_verify_otp")


@require_http_methods(["GET", "POST"])
def farmer_signup(request):
    if not request.session.get("phone_otp_verified"):
        message = "Please verify your phone first."
        if is_ajax(request):
            return json_error(
                message,
                extra={"redirect_url": reverse("accounts:farmer_request_otp")},
            )
        messages.error(request, message)
        return redirect("accounts:farmer_request_otp")

    verified_phone = normalize_ugandan_phone(request.session.get("verified_phone"))

    if not verified_phone:
        message = "Your verification session expired. Please verify your phone again."
        if is_ajax(request):
            return json_error(
                message,
                extra={"redirect_url": reverse("accounts:farmer_request_otp")},
            )
        messages.error(request, message)
        return redirect("accounts:farmer_request_otp")

    form = FarmerSignupForm(request.POST or None)

    if request.method == "POST":
        if not form.is_valid():
            if is_ajax(request):
                return json_error(
                    "Please correct the highlighted errors.",
                    errors=form_errors(form),
                )
            return render(
                request,
                "accounts/farmer_signup.html",
                {"form": form, "verified_phone": verified_phone},
            )

        if User.objects.filter(phone=verified_phone).exists():
            message = "An account with this phone number already exists."
            if is_ajax(request):
                return json_error(message)
            messages.error(request, message)
            return render(
                request,
                "accounts/farmer_signup.html",
                {"form": form, "verified_phone": verified_phone},
            )

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

        redirect_url = reverse("marketplace:listing_list")
        message = "Farmer account created successfully."

        if is_ajax(request):
            return json_success(redirect_url=redirect_url, message=message)

        messages.success(request, message)
        return redirect("marketplace:listing_list")

    return render(
        request,
        "accounts/farmer_signup.html",
        {"form": form, "verified_phone": verified_phone},
    )


@require_http_methods(["GET", "POST"])
def farmer_login(request):
    form = FarmerLoginForm(request.POST or None, request=request)

    if request.method == "POST":
        if form.is_valid():
            user = form.cleaned_data["user"]
            safe_login(request, user)

            redirect_url = reverse("marketplace:listing_list")

            if is_ajax(request):
                return json_success(
                    redirect_url=redirect_url,
                    message="Login successful.",
                )

            return redirect("marketplace:listing_list")

        if is_ajax(request):
            return json_error(
                "Invalid phone number or password.",
                errors=form_errors(form),
            )

    return render(request, "accounts/farmer_login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def business_signup(request):
    form = BusinessSignupForm(request.POST or None)

    if request.method == "POST":
        if not form.is_valid():
            if is_ajax(request):
                return json_error(
                    "Please correct the highlighted errors.",
                    errors=form_errors(form),
                )
            return render(request, "accounts/business_signup.html", {"form": form})

        user = create_business_account(
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
            district=form.cleaned_data.get("district"),
            verified=True,
        )

        safe_login(request, user)

        redirect_url = reverse("marketplace:listing_list")
        message = "Business account created successfully."

        if is_ajax(request):
            return json_success(redirect_url=redirect_url, message=message)

        messages.success(request, message)
        return redirect("marketplace:listing_list")

    return render(request, "accounts/business_signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def business_login(request):
    form = BusinessLoginForm(request.POST or None, request=request)

    if request.method == "POST":
        if form.is_valid():
            user = form.cleaned_data["user"]
            safe_login(request, user)

            redirect_url = reverse("marketplace:listing_list")

            if is_ajax(request):
                return json_success(
                    redirect_url=redirect_url,
                    message="Login successful.",
                )

            return redirect("marketplace:listing_list")

        if is_ajax(request):
            return json_error(
                "Invalid email or password.",
                errors=form_errors(form),
            )

    return render(request, "accounts/business_login.html", {"form": form})


def logout_view(request):
    logout(request)

    if is_ajax(request):
        return json_success(
            redirect_url=reverse("core:home"),
            message="Logged out successfully.",
        )

    return redirect("core:home")