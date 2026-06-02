from django import forms
from django.contrib.auth import authenticate

from core.forms import apply_tailwind_classes
from .models import User, AccountTypeChoices
from .utils import normalize_ugandan_phone, is_valid_ugandan_phone


class FarmerPhoneForm(forms.Form):
    phone = forms.CharField(max_length=20, label="Phone Number")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)

    def clean_phone(self):
        phone = normalize_ugandan_phone(self.cleaned_data["phone"])
        if not is_valid_ugandan_phone(phone):
            raise forms.ValidationError("Enter a valid Ugandan phone number.")
        return phone


class OTPVerificationForm(forms.Form):
    code = forms.CharField(max_length=20, label="OTP Code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)

    def clean_code(self):
        raw_code = self.cleaned_data.get("code", "")
        code = "".join(ch for ch in raw_code.strip() if ch.isdigit())

        if len(code) != 6:
            raise forms.ValidationError("Enter a valid 6-digit OTP code.")

        return code


class FarmerSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = User
        fields = ["full_name", "district"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm_password = cleaned.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned


class FarmerLoginForm(forms.Form):
    phone = forms.CharField(max_length=20, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)

    def clean_phone(self):
        return normalize_ugandan_phone(self.cleaned_data["phone"])

    def clean(self):
        cleaned = super().clean()
        phone = cleaned.get("phone")
        password = cleaned.get("password")

        if phone and password:
            user = authenticate(self.request, username=phone, password=password)

            if not user:
                raise forms.ValidationError("Invalid phone number or password.")

            if user.account_type != AccountTypeChoices.FARMER:
                raise forms.ValidationError("This login is for farmer accounts only.")

            cleaned["user"] = user

        return cleaned


class BusinessSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = User
        fields = ["full_name", "email", "district"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")

        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm_password = cleaned.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned


class BusinessLoginForm(forms.Form):
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        apply_tailwind_classes(self)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")

        if email and password:
            user = authenticate(self.request, username=email, password=password)

            if not user:
                raise forms.ValidationError("Invalid email or password.")

            if user.account_type != AccountTypeChoices.BUSINESS:
                raise forms.ValidationError("This login is for business accounts only.")

            cleaned["user"] = user

        return cleaned
