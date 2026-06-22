from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model

from farms.models import (
    Farm, FarmActivity, HarvestRecord, FarmExpense, SalesRecord,
    FarmProject, ProductionBatch, ProjectPlannedActivity, ProjectInputRecord, ProjectRevenueRecord,
)
from marketplace.models import ProduceListing, ProduceListingImage, BuyerRequest, ListingInquiry, MarketplacePurchase

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

    if "@" in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
        if user:
            return user

    for phone in _phone_candidates(identifier):
        user = User.objects.filter(phone=phone).first()
        if user:
            return user

    try:
        return User.objects.filter(username__iexact=identifier).first()
    except Exception:
        return None


class AccountRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=6)
    phone = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    account_type = serializers.ChoiceField(choices=[("farmer", "Farmer"), ("guest", "Guest")], default="farmer")

    def validate(self, attrs):
        phone = str(attrs.get("phone") or "").strip()
        email = str(attrs.get("email") or "").strip().lower()
        if not phone and not email:
            raise serializers.ValidationError("Provide either phone or email.")
        if phone:
            candidates = _phone_candidates(phone)
            phone = next((p for p in candidates if p.startswith("+256")), phone)
            if User.objects.filter(phone__in=candidates).exists():
                raise serializers.ValidationError({"phone": "This phone number is already registered."})
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})
        attrs["phone"] = phone or None
        attrs["email"] = email or None
        return attrs

    def create(self, validated_data):
        from accounts.services import create_farmer_account

        password = validated_data.pop("password")
        account_type = validated_data.pop("account_type", "farmer")
        if account_type != "farmer":
            raise serializers.ValidationError({"account_type": "Only farmer registration is supported by this endpoint."})

        return create_farmer_account(
            full_name=validated_data.get("full_name"),
            password=password,
            phone=validated_data.get("phone"),
            email=validated_data.get("email"),
            district=validated_data.get("district"),
            verified=True,
        )


class FarmerLoginSerializer(serializers.Serializer):
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
            login_key = getattr(user_obj, User.USERNAME_FIELD, None) or user_obj.email or user_obj.phone
            user = authenticate(self.context.get("request"), username=login_key, password=password)
            if user is None and user_obj.email:
                user = authenticate(self.context.get("request"), username=user_obj.email, password=password)
            if user is None and user_obj.phone:
                user = authenticate(self.context.get("request"), username=user_obj.phone, password=password)
            if user is None and user_obj.check_password(password):
                user = user_obj
        else:
            user = authenticate(self.context.get("request"), username=identifier, password=password)

        if not user:
            raise serializers.ValidationError("Invalid login credentials.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        if getattr(user, "account_type", None) not in ["farmer", "guest", "admin"]:
            raise serializers.ValidationError("Only farmer or guest accounts can use this API.")

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


class FarmerOwnedModelSerializer(OfflineModelSerializer):
    """Base serializer for models that belong to the logged-in farmer.

    It attaches request.user before validation/save so API creates do not hit
    `RelatedObjectDoesNotExist: <Model> has no farmer`, and it prevents mobile
    clients from posting another farmer's farm/project IDs.
    """
    farmer = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return attrs

        farm = attrs.get("farm") or getattr(self.instance, "farm", None)
        project = attrs.get("project") or getattr(self.instance, "project", None)
        harvest = attrs.get("harvest") or getattr(self.instance, "harvest", None)
        batch = attrs.get("batch") or getattr(self.instance, "batch", None)

        if batch:
            if getattr(batch, "farmer_id", None) != user.id:
                raise serializers.ValidationError({"batch": "This batch does not belong to your account."})
            attrs["project"] = batch.project
            attrs["farm"] = batch.farm
            project = batch.project
            farm = batch.farm

        if project and not farm:
            attrs["farm"] = project.farm
            farm = project.farm

        if harvest:
            if getattr(harvest, "farmer_id", None) != user.id:
                raise serializers.ValidationError({"harvest": "This harvest does not belong to your account."})
            if not project and getattr(harvest, "project", None):
                attrs["project"] = harvest.project
                project = harvest.project
            if not farm and getattr(harvest, "farm", None):
                attrs["farm"] = harvest.farm
                farm = harvest.farm

        if farm and getattr(farm, "farmer_id", None) != user.id:
            raise serializers.ValidationError({"farm": "This farm does not belong to your account."})
        if project and getattr(project, "farmer_id", None) != user.id:
            raise serializers.ValidationError({"project": "This project does not belong to your account."})
        if project and farm and getattr(project, "farm_id", None) != getattr(farm, "id", None):
            raise serializers.ValidationError({"project": "The selected project must belong to the selected farm."})
        if batch and project and getattr(batch, "project_id", None) != getattr(project, "id", None):
            raise serializers.ValidationError({"batch": "The selected batch must belong to the selected project."})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and getattr(request, "user", None) and getattr(request.user, "is_authenticated", False):
            validated_data["farmer"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and getattr(request, "user", None) and getattr(request.user, "is_authenticated", False):
            validated_data["farmer"] = request.user
        return super().update(instance, validated_data)


class FarmSerializer(FarmerOwnedModelSerializer):
    class Meta:
        model = Farm
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "sync_status"]


class ProjectLinkedSerializer(FarmerOwnedModelSerializer):
    class Meta:
        abstract = True
        extra_kwargs = {
            "farm": {"required": False, "allow_null": True},
        }


class FarmActivitySerializer(ProjectLinkedSerializer):
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FarmActivity
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "sync_status", "total_cost"]
        extra_kwargs = {"farm": {"required": False, "allow_null": True}}


class HarvestRecordSerializer(ProjectLinkedSerializer):
    class Meta:
        model = HarvestRecord
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "sync_status"]
        extra_kwargs = {"farm": {"required": False, "allow_null": True}}


class FarmExpenseSerializer(ProjectLinkedSerializer):
    class Meta:
        model = FarmExpense
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "sync_status"]
        extra_kwargs = {"farm": {"required": False, "allow_null": True}}


class SalesRecordSerializer(ProjectLinkedSerializer):
    class Meta:
        model = SalesRecord
        fields = "__all__"
        read_only_fields = ["total_amount", "created_at", "updated_at", "sync_status"]
        extra_kwargs = {"farm": {"required": False, "allow_null": True}}


class FarmProjectSerializer(FarmerOwnedModelSerializer):
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
            "created_at", "updated_at", "sync_status",
            "planned_profit", "actual_cost", "actual_revenue",
            "estimated_profit", "projected_profit", "cost_variance",
        ]


class ProductionBatchSerializer(FarmerOwnedModelSerializer):
    display_name = serializers.CharField(read_only=True)
    actual_expenses = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    actual_revenue = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    profit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    harvested_quantity = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    sold_quantity = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    stock_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProductionBatch
        fields = "__all__"
        read_only_fields = [
            "created_at", "updated_at", "sync_status", "display_name",
            "actual_expenses", "actual_revenue", "profit", "harvested_quantity",
            "sold_quantity", "stock_balance",
        ]


class ProjectPlannedActivitySerializer(ProjectLinkedSerializer):
    cost_variance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProjectPlannedActivity
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "sync_status", "cost_variance"]
        extra_kwargs = {"farm": {"required": False, "allow_null": True}}


class ProjectInputRecordSerializer(ProjectLinkedSerializer):
    class Meta:
        model = ProjectInputRecord
        fields = "__all__"
        read_only_fields = ["total_cost", "created_at", "updated_at", "sync_status"]
        extra_kwargs = {"farm": {"required": False, "allow_null": True}}


class ProjectRevenueRecordSerializer(ProjectLinkedSerializer):
    class Meta:
        model = ProjectRevenueRecord
        fields = "__all__"
        read_only_fields = ["amount", "created_at", "updated_at", "sync_status"]
        extra_kwargs = {"farm": {"required": False, "allow_null": True}}


class ProduceListingImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProduceListingImage
        fields = ["id", "image", "image_url", "is_primary", "sort_order", "created_at", "updated_at"]
        read_only_fields = ["id", "image_url", "created_at", "updated_at"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        url = obj.image.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class ProduceListingSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source="farmer.full_name", read_only=True)
    pin_type = serializers.SerializerMethodField()
    images = ProduceListingImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="Upload one or more product images using multipart/form-data. Use field name uploaded_images.",
    )
    primary_image_url = serializers.SerializerMethodField()

    def get_pin_type(self, obj):
        return "farmer"

    def get_primary_image_url(self, obj):
        image = None
        try:
            image = obj.images.filter(is_primary=True).first() or obj.images.first()
        except Exception:
            image = None
        if not image or not image.image:
            return None
        url = image.image.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    class Meta:
        model = ProduceListing
        fields = "__all__"
        read_only_fields = ["farmer", "created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        farm = attrs.get("farm") or getattr(self.instance, "farm", None)
        if farm and user and getattr(user, "is_authenticated", False) and getattr(farm, "farmer_id", None) != user.id:
            raise serializers.ValidationError({"farm": "This farm does not belong to your account."})
        return attrs

    def _create_images(self, listing, images):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not images or not user or not getattr(user, "is_authenticated", False):
            return
        already_has_primary = listing.images.filter(is_primary=True).exists()
        start_order = listing.images.count()
        for index, image in enumerate(images):
            ProduceListingImage.objects.create(
                listing=listing,
                uploaded_by=user,
                image=image,
                is_primary=(not already_has_primary and index == 0),
                sort_order=start_order + index,
            )

    def create(self, validated_data):
        images = validated_data.pop("uploaded_images", [])
        listing = super().create(validated_data)
        self._create_images(listing, images)
        return listing

    def update(self, instance, validated_data):
        images = validated_data.pop("uploaded_images", [])
        listing = super().update(instance, validated_data)
        self._create_images(listing, images)
        return listing


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


class MarketplacePurchaseSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.full_name", read_only=True)
    listing_name = serializers.CharField(source="listing.crop_name", read_only=True)
    farmer_name = serializers.CharField(source="listing.farmer.full_name", read_only=True)

    class Meta:
        model = MarketplacePurchase
        fields = "__all__"
        read_only_fields = ["buyer", "total_amount", "status", "created_at", "updated_at"]
