from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model

from farms.models import (
    Farm, FarmActivity, HarvestRecord, FarmExpense, SalesRecord,
    FarmProject, ProjectPlannedActivity, ProjectInputRecord, ProjectRevenueRecord,
)
from marketplace.models import ProduceListing, BuyerRequest, ListingInquiry

User = get_user_model()


def _phone_candidates(value: str) -> list[str]:
    """Return common Uganda phone formats so web and mobile login behave the same."""
    raw = str(value or "").strip().replace(" ", "")
    if not raw:
        return []
    candidates = {raw}
    digits = raw.replace("+", "")
    if digits.startswith("256") and len(digits) >= 12:
        candidates.add("0" + digits[3:])
        candidates.add("+" + digits)
    elif digits.startswith("0") and len(digits) >= 10:
        candidates.add("256" + digits[1:])
        candidates.add("+256" + digits[1:])
    elif len(digits) == 9:
        candidates.add("0" + digits)
        candidates.add("256" + digits)
        candidates.add("+256" + digits)
    return list(candidates)


def _find_user_by_identifier(identifier: str):
    identifier = str(identifier or "").strip()
    if not identifier:
        return None

    # Email login
    if "@" in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
        if user:
            return user

    # Phone login, including 077..., 25677..., +25677..., 77...
    for phone in _phone_candidates(identifier):
        user = User.objects.filter(phone=phone).first()
        if user:
            return user

    # Last fallback for projects that still have a username field/custom migration.
    try:
        return User.objects.filter(username__iexact=identifier).first()
    except Exception:
        return None


class FarmerLoginSerializer(serializers.Serializer):
    # Mobile app sends `identifier`. Older builds may still send `username`, `phone`, `email`, or `phone_or_email`.
    identifier = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    phone_or_email = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = (
            attrs.get("identifier")
            or attrs.get("username")
            or attrs.get("phone_or_email")
            or attrs.get("phone")
            or attrs.get("email")
        )
        password = attrs.get("password")

        if not identifier or not password:
            raise serializers.ValidationError("Phone, email or username and password are required.")

        user_obj = _find_user_by_identifier(identifier)
        user = None

        if user_obj:
            # The custom User model uses email as USERNAME_FIELD, so authenticate with email first.
            login_key = getattr(user_obj, User.USERNAME_FIELD, None) or user_obj.email or user_obj.phone
            user = authenticate(self.context.get("request"), username=login_key, password=password)
            if user is None and user_obj.email:
                user = authenticate(self.context.get("request"), username=user_obj.email, password=password)
            if user is None and user_obj.phone:
                user = authenticate(self.context.get("request"), username=user_obj.phone, password=password)

            # Safe fallback: same password check as web backend, useful where USERNAME_FIELD differs.
            if user is None and user_obj.check_password(password):
                user = user_obj
        else:
            # Fallback through configured auth backends.
            user = authenticate(self.context.get("request"), username=identifier, password=password)

        if not user:
            raise serializers.ValidationError("Invalid login credentials.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        if getattr(user, "account_type", None) not in ["farmer", "admin"]:
            raise serializers.ValidationError("Only farmer accounts can use this mobile API.")

        attrs["user"] = user
        return attrs


class FarmerProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.EmailField(read_only=True, allow_null=True)
    district = serializers.CharField(read_only=True, allow_null=True)
    account_type = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)


class OfflineModelSerializer(serializers.ModelSerializer):
    client_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    client_updated_at = serializers.DateTimeField(required=False, allow_null=True)
    sync_status = serializers.CharField(read_only=True)
    is_deleted = serializers.BooleanField(required=False)


class FarmSerializer(OfflineModelSerializer):
    class Meta:
        model = Farm
        fields = "__all__"
        read_only_fields = ["farmer", "created_at", "updated_at", "sync_status"]


class FarmActivitySerializer(OfflineModelSerializer):
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FarmActivity
        fields = "__all__"
        read_only_fields = ["farmer", "created_at", "updated_at", "sync_status", "total_cost"]


class HarvestRecordSerializer(OfflineModelSerializer):
    class Meta:
        model = HarvestRecord
        fields = "__all__"
        read_only_fields = ["farmer", "created_at", "updated_at", "sync_status"]


class FarmExpenseSerializer(OfflineModelSerializer):
    class Meta:
        model = FarmExpense
        fields = "__all__"
        read_only_fields = ["farmer", "created_at", "updated_at", "sync_status"]


class SalesRecordSerializer(OfflineModelSerializer):
    class Meta:
        model = SalesRecord
        fields = "__all__"
        read_only_fields = ["farmer", "total_amount", "created_at", "updated_at", "sync_status"]




class FarmProjectSerializer(OfflineModelSerializer):
    planned_profit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    actual_cost = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    actual_revenue = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    estimated_profit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    projected_profit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    cost_variance = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = FarmProject
        fields = "__all__"
        read_only_fields = [
            "farmer", "created_at", "updated_at", "sync_status",
            "planned_profit", "actual_cost", "actual_revenue",
            "estimated_profit", "projected_profit", "cost_variance",
        ]


class ProjectPlannedActivitySerializer(OfflineModelSerializer):
    cost_variance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProjectPlannedActivity
        fields = "__all__"
        read_only_fields = ["farmer", "created_at", "updated_at", "sync_status", "cost_variance"]


class ProjectInputRecordSerializer(OfflineModelSerializer):
    class Meta:
        model = ProjectInputRecord
        fields = "__all__"
        read_only_fields = ["farmer", "total_cost", "created_at", "updated_at", "sync_status"]


class ProjectRevenueRecordSerializer(OfflineModelSerializer):
    class Meta:
        model = ProjectRevenueRecord
        fields = "__all__"
        read_only_fields = ["farmer", "amount", "created_at", "updated_at", "sync_status"]


class ProduceListingSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source="farmer.full_name", read_only=True)
    pin_type = serializers.SerializerMethodField()

    def get_pin_type(self, obj):
        return "farmer"

    class Meta:
        model = ProduceListing
        fields = "__all__"
        read_only_fields = ["farmer", "created_at", "updated_at"]


class BuyerRequestSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="business_user.full_name", read_only=True)
    pin_type = serializers.SerializerMethodField()

    def get_pin_type(self, obj):
        return "buyer"

    class Meta:
        model = BuyerRequest
        fields = "__all__"
        read_only_fields = ["business_user", "created_at", "updated_at"]


class ListingInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingInquiry
        fields = "__all__"
        read_only_fields = ["business_user", "created_at", "updated_at", "status"]
