from django.db import IntegrityError, transaction
from django.db.models import Sum, Q, Count
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models.functions import TruncMonth
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

from farms.models import (
    Farm, FarmActivity, HarvestRecord, FarmExpense, SalesRecord,
    FarmProject, ProjectPlannedActivity, ProjectInputRecord, ProjectRevenueRecord,
)
from marketplace.models import ProduceListing, BuyerRequest, ListingInquiry, MarketplacePurchase, ListingStatusChoices, RequestStatusChoices

from .serializers import (
    AccountRegistrationSerializer,
    FarmerLoginSerializer,
    FarmerProfileSerializer,
    FarmSerializer,
    FarmActivitySerializer,
    HarvestRecordSerializer,
    FarmExpenseSerializer,
    SalesRecordSerializer,
    FarmProjectSerializer,
    ProjectPlannedActivitySerializer,
    ProjectInputRecordSerializer,
    ProjectRevenueRecordSerializer,
    ProduceListingSerializer,
    BuyerRequestSerializer,
    ListingInquirySerializer,
    MarketplacePurchaseSerializer,
)


class AccountRegistrationAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "message": "Account created successfully",
            "token": token.key,
            "user": FarmerProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class FarmerLoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = FarmerLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "message": "Login successful",
            "token": token.key,
            "user": FarmerProfileSerializer(user).data,
        }, status=status.HTTP_200_OK)


class FarmerLogoutAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"message": "Logged out successfully"})


class FarmerProfileAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(FarmerProfileSerializer(request.user).data)


class FarmerDashboardAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        farms = Farm.objects.filter(farmer=user, is_deleted=False)
        activities = FarmActivity.objects.filter(farmer=user, is_deleted=False)
        harvests = HarvestRecord.objects.filter(farmer=user, is_deleted=False)
        expenses = FarmExpense.objects.filter(farmer=user, is_deleted=False)
        sales = SalesRecord.objects.filter(farmer=user, is_deleted=False)
        total_harvest = harvests.aggregate(total=Sum("actual_yield"))["total"] or 0
        activity_totals = activities.aggregate(labour=Sum("labour_cost"), inputs=Sum("input_cost"))
        total_activity_cost = (activity_totals["labour"] or 0) + (activity_totals["inputs"] or 0)
        total_expenses = expenses.aggregate(total=Sum("amount"))["total"] or 0
        total_sales = sales.aggregate(total=Sum("total_amount"))["total"] or 0
        profit = total_sales - total_expenses - total_activity_cost

        projects = FarmProject.objects.filter(farmer=user, is_deleted=False)
        project_inputs = ProjectInputRecord.objects.filter(farmer=user, is_deleted=False)
        project_revenues = ProjectRevenueRecord.objects.filter(farmer=user, is_deleted=False)
        planned_activities = ProjectPlannedActivity.objects.filter(farmer=user, is_deleted=False)
        project_expected_revenue = projects.aggregate(total=Sum("expected_revenue"))["total"] or 0
        project_expected_cost = projects.aggregate(total=Sum("expected_cost"))["total"] or 0
        project_actual_cost = project_inputs.aggregate(total=Sum("total_cost"))["total"] or 0
        project_actual_revenue = project_revenues.aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "farms_count": farms.count(),
            "activities_count": activities.count(),
            "harvests_count": harvests.count(),
            "expenses_count": expenses.count(),
            "sales_count": sales.count(),
            "total_harvest": total_harvest,
            "total_activity_cost": total_activity_cost,
            "total_expenses": total_expenses,
            "total_sales": total_sales,
            "estimated_profit": profit,
            "projects_count": projects.count(),
            "active_projects_count": projects.filter(status="active").count(),
            "planned_project_profit": project_expected_revenue - project_expected_cost,
            "project_actual_cost": project_actual_cost,
            "project_actual_revenue": project_actual_revenue,
            "project_estimated_profit": project_actual_revenue - project_actual_cost,
            "project_projected_profit": project_expected_revenue - project_actual_cost,
            "pending_planned_activities": planned_activities.filter(status__in=["todo", "in_progress"]).count(),
        })


class FarmerOwnedViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        qs = self.model.objects.filter(farmer=self.request.user)
        if self.request.query_params.get("include_deleted") != "true":
            qs = qs.filter(is_deleted=False)
        updated_since = self.request.query_params.get("updated_since")
        if updated_since:
            dt = parse_datetime(updated_since)
            if dt:
                qs = qs.filter(updated_at__gt=dt)
        return qs

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user, sync_status="synced")

    def perform_update(self, serializer):
        serializer.save(farmer=self.request.user, sync_status="synced")

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.sync_status = "synced"
        instance.save(update_fields=["is_deleted", "sync_status", "updated_at"])


class FarmViewSet(FarmerOwnedViewSet):
    model = Farm
    serializer_class = FarmSerializer


class FarmActivityViewSet(FarmerOwnedViewSet):
    model = FarmActivity
    serializer_class = FarmActivitySerializer


class HarvestRecordViewSet(FarmerOwnedViewSet):
    model = HarvestRecord
    serializer_class = HarvestRecordSerializer


class FarmExpenseViewSet(FarmerOwnedViewSet):
    model = FarmExpense
    serializer_class = FarmExpenseSerializer


class SalesRecordViewSet(FarmerOwnedViewSet):
    model = SalesRecord
    serializer_class = SalesRecordSerializer




class FarmProjectViewSet(FarmerOwnedViewSet):
    model = FarmProject
    serializer_class = FarmProjectSerializer

    @action(detail=True, methods=["get"], url_path="profit-summary")
    def profit_summary(self, request, id=None):
        project = self.get_object()
        inputs = project.input_records.filter(is_deleted=False)
        revenues = project.revenue_records.filter(is_deleted=False)
        plans = project.planned_activities.filter(is_deleted=False)

        input_by_category = list(
            inputs.values("category")
            .annotate(total=Sum("total_cost"), count=Count("id"))
            .order_by("category")
        )
        monthly_inputs = list(
            inputs.annotate(month=TruncMonth("record_date"))
            .values("month", "category")
            .annotate(total=Sum("total_cost"))
            .order_by("month", "category")
        )

        return Response({
            "project_id": project.id,
            "project_name": project.name,
            "status": project.status,
            "expected_revenue": project.expected_revenue,
            "expected_cost": project.expected_cost,
            "planned_profit": project.planned_profit,
            "actual_cost": project.actual_cost,
            "actual_revenue": project.actual_revenue,
            "estimated_profit": project.estimated_profit,
            "projected_profit": project.projected_profit,
            "cost_variance": project.cost_variance,
            "input_by_category": input_by_category,
            "monthly_inputs": monthly_inputs,
            "planned_activities": {
                "todo": plans.filter(status="todo").count(),
                "in_progress": plans.filter(status="in_progress").count(),
                "done": plans.filter(status="done").count(),
                "missed": plans.filter(status="missed").count(),
                "cancelled": plans.filter(status="cancelled").count(),
            },
            "revenue_records_count": revenues.count(),
            "input_records_count": inputs.count(),
        })


class ProjectPlannedActivityViewSet(FarmerOwnedViewSet):
    model = ProjectPlannedActivity
    serializer_class = ProjectPlannedActivitySerializer


class ProjectInputRecordViewSet(FarmerOwnedViewSet):
    model = ProjectInputRecord
    serializer_class = ProjectInputRecordSerializer


class ProjectRevenueRecordViewSet(FarmerOwnedViewSet):
    model = ProjectRevenueRecord
    serializer_class = ProjectRevenueRecordSerializer


class ProjectPlannerAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        project_id = request.query_params.get("project")
        plans = ProjectPlannedActivity.objects.filter(farmer=user, is_deleted=False)
        if project_id:
            plans = plans.filter(project_id=project_id)

        upcoming = plans.filter(status__in=["todo", "in_progress"]).order_by("planned_date")[:20]
        overdue = plans.filter(status__in=["todo", "in_progress"], planned_date__lt=timezone.localdate()).count()
        return Response({
            "upcoming": ProjectPlannedActivitySerializer(upcoming, many=True).data,
            "overdue_count": overdue,
            "todo_count": plans.filter(status="todo").count(),
            "in_progress_count": plans.filter(status="in_progress").count(),
            "done_count": plans.filter(status="done").count(),
            "missed_count": plans.filter(status="missed").count(),
        })


class ProjectInputTrendsAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = ProjectInputRecord.objects.filter(farmer=user, is_deleted=False)
        project_id = request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)

        rows = list(
            qs.annotate(month=TruncMonth("record_date"))
            .values("month", "category")
            .annotate(total=Sum("total_cost"), quantity=Sum("quantity"))
            .order_by("category", "month")
        )

        previous_by_category = {}
        trends = []
        for row in rows:
            category = row["category"]
            total = row["total"] or 0
            previous = previous_by_category.get(category)
            change = None if previous is None else total - previous
            direction = "same"
            if change is not None and change > 0:
                direction = "increase"
            elif change is not None and change < 0:
                direction = "decrease"
            trends.append({
                "month": row["month"],
                "category": category,
                "total": total,
                "quantity": row["quantity"] or 0,
                "previous_total": previous,
                "change": change,
                "direction": direction,
            })
            previous_by_category[category] = total

        category_totals = list(
            qs.values("category")
            .annotate(total=Sum("total_cost"), quantity=Sum("quantity"), records=Count("id"))
            .order_by("-total")
        )
        return Response({"trends": trends, "category_totals": category_totals})


def _decimal_param(value):
    if value in [None, ""]:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def apply_market_filters(qs, request, is_listing=True):
    crop = request.query_params.get("crop") or request.query_params.get("product")
    district = request.query_params.get("district") or request.query_params.get("location")
    min_price = _decimal_param(request.query_params.get("min_price"))
    max_price = _decimal_param(request.query_params.get("max_price"))
    min_qty = _decimal_param(request.query_params.get("min_quantity"))
    max_qty = _decimal_param(request.query_params.get("max_quantity"))

    if crop:
        qs = qs.filter(crop_name__icontains=crop)
    if district:
        if is_listing:
            qs = qs.filter(Q(district__icontains=district) | Q(subcounty__icontains=district) | Q(village__icontains=district))
        else:
            qs = qs.filter(Q(delivery_district__icontains=district) | Q(delivery_location__icontains=district))

    price_field = "expected_price" if is_listing else "max_price"
    qty_field = "quantity" if is_listing else "quantity_needed"
    if min_price is not None:
        qs = qs.filter(**{f"{price_field}__gte": min_price})
    if max_price is not None:
        qs = qs.filter(**{f"{price_field}__lte": max_price})
    if min_qty is not None:
        qs = qs.filter(**{f"{qty_field}__gte": min_qty})
    if max_qty is not None:
        qs = qs.filter(**{f"{qty_field}__lte": max_qty})
    return qs


class MarketplaceMapAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        listings = apply_market_filters(
            ProduceListing.objects.filter(status=ListingStatusChoices.OPEN, latitude__isnull=False, longitude__isnull=False)
            .select_related("farmer", "farm"),
            request,
            is_listing=True,
        )
        buyer_requests = apply_market_filters(
            BuyerRequest.objects.filter(status=RequestStatusChoices.OPEN, latitude__isnull=False, longitude__isnull=False)
            .select_related("business_user"),
            request,
            is_listing=False,
        )
        pins = []
        for item in listings[:300]:
            pins.append({
                "id": str(item.id),
                "pin_type": "farmer",
                "title": item.crop_name,
                "name": getattr(item.farmer, "full_name", "Farmer"),
                "quantity": str(item.quantity),
                "unit": item.unit,
                "price": str(item.expected_price or ""),
                "district": item.district,
                "location": ", ".join([x for x in [item.village, item.subcounty, item.district] if x]),
                "latitude": float(item.latitude),
                "longitude": float(item.longitude),
                "status": item.status,
                "description": item.description or "",
            })
        for item in buyer_requests[:300]:
            pins.append({
                "id": str(item.id),
                "pin_type": "buyer",
                "title": item.crop_name,
                "name": getattr(item.business_user, "full_name", "Buyer"),
                "quantity": str(item.quantity_needed),
                "unit": item.unit,
                "price": str(item.max_price or item.min_price or ""),
                "district": item.delivery_district or "",
                "location": item.delivery_location or item.delivery_district or "",
                "latitude": float(item.latitude),
                "longitude": float(item.longitude),
                "status": item.status,
                "description": item.notes or "",
            })
        return Response({"count": len(pins), "pins": pins})

class ProduceListingViewSet(viewsets.ModelViewSet):
    serializer_class = ProduceListingSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ProduceListing.objects.filter(farmer=self.request.user)
        qs = apply_market_filters(qs, self.request, is_listing=True)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)


class OpenBuyerRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BuyerRequestSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = BuyerRequest.objects.filter(status=RequestStatusChoices.OPEN)
        return apply_market_filters(qs, self.request, is_listing=False)


class ListingInquiryViewSet(viewsets.ModelViewSet):
    serializer_class = ListingInquirySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ListingInquiry.objects.filter(listing__farmer=self.request.user)


class OpenProduceListingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProduceListingSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ProduceListing.objects.filter(status=ListingStatusChoices.OPEN).select_related("farmer", "farm")
        return apply_market_filters(qs, self.request, is_listing=True)


class MarketplacePurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = MarketplacePurchaseSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "account_type", None) == "farmer":
            return MarketplacePurchase.objects.filter(listing__farmer=user).select_related("listing", "buyer")
        return MarketplacePurchase.objects.filter(buyer=user).select_related("listing", "buyer")

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)


class FarmerOfflineSyncAPIView(APIView):
    """One endpoint for mobile apps to upload local changes and download server changes.

    Request format:
    {
      "last_sync_at": "2026-05-22T10:00:00Z",
      "farms": [{...}], "activities": [{...}], "harvests": [{...}], "expenses": [{...}], "sales": [{...}]
    }
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    sync_map = {
        "farms": (Farm, FarmSerializer),
        "activities": (FarmActivity, FarmActivitySerializer),
        "harvests": (HarvestRecord, HarvestRecordSerializer),
        "expenses": (FarmExpense, FarmExpenseSerializer),
        "sales": (SalesRecord, SalesRecordSerializer),
        "projects": (FarmProject, FarmProjectSerializer),
        "project_plans": (ProjectPlannedActivity, ProjectPlannedActivitySerializer),
        "project_inputs": (ProjectInputRecord, ProjectInputRecordSerializer),
        "project_revenues": (ProjectRevenueRecord, ProjectRevenueRecordSerializer),
    }

    def post(self, request):
        user = request.user
        uploaded, errors = {}, {}
        with transaction.atomic():
            for key, (model, serializer_class) in self.sync_map.items():
                uploaded[key] = []
                errors[key] = []
                for item in request.data.get(key, []):
                    instance = None
                    client_id = item.get("client_id")
                    server_id = item.get("id")
                    if server_id:
                        instance = model.objects.filter(id=server_id, farmer=user).first()
                    if instance is None and client_id:
                        instance = model.objects.filter(client_id=client_id, farmer=user).first()
                    serializer = serializer_class(instance, data=item, partial=bool(instance), context={"request": request})
                    if serializer.is_valid():
                        try:
                            obj = serializer.save(farmer=user, sync_status="synced")
                            uploaded[key].append(serializer_class(obj, context={"request": request}).data)
                        except IntegrityError as exc:
                            errors[key].append({"client_id": client_id, "error": str(exc)})
                    else:
                        errors[key].append({"client_id": client_id, "error": serializer.errors})

        last_sync_at = request.data.get("last_sync_at") or request.query_params.get("last_sync_at")
        dt = parse_datetime(last_sync_at) if last_sync_at else None
        download = {}
        for key, (model, serializer_class) in self.sync_map.items():
            qs = model.objects.filter(farmer=user)
            if dt:
                qs = qs.filter(updated_at__gt=dt)
            download[key] = serializer_class(qs, many=True, context={"request": request}).data

        from django.utils import timezone
        return Response({
            "server_time": timezone.now().isoformat(),
            "uploaded": uploaded,
            "download": download,
            "errors": errors,
        })
