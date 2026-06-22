from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Min
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import CompanyProductPriceForm, MarketPriceForm
from .models import CompanyProductPrice, MarketPrice


@login_required
def market_price_list(request):
    prices = MarketPrice.objects.all()
    return render(request, "prices/market_price_list.html", {"prices": prices})


@login_required
def market_price_create(request):
    form = MarketPriceForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            price = form.save(commit=False)
            price.entered_by = request.user
            price.save()

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": "Market price added successfully."})

            messages.success(request, "Market price added successfully.")
            return redirect("prices:market_price_list")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return render(request, "prices/market_price_form.html", {"form": form, "title": "Add Market Price"})


@login_required
def company_price_compare(request):
    product = request.GET.get("product", "").strip()
    district = request.GET.get("district", "").strip()
    unit = request.GET.get("unit", "").strip()

    prices = CompanyProductPrice.objects.filter(is_active=True)
    if product:
        prices = prices.filter(product_name__icontains=product)
    if district:
        prices = prices.filter(district__icontains=district)
    if unit:
        prices = prices.filter(unit=unit)

    prices = prices.order_by("-price_per_unit", "company_name")
    best_price = prices.first()

    summary = prices.aggregate(
        company_count=Count("company_name", distinct=True),
        highest_price=Max("price_per_unit"),
        lowest_price=Min("price_per_unit"),
        average_price=Avg("price_per_unit"),
    )

    spread_amount = Decimal("0")
    spread_percent = Decimal("0")
    if summary["highest_price"] is not None and summary["lowest_price"] is not None:
        spread_amount = summary["highest_price"] - summary["lowest_price"]
        if summary["lowest_price"] > 0:
            spread_percent = (spread_amount / summary["lowest_price"]) * Decimal("100")

    products = (
        CompanyProductPrice.objects.filter(is_active=True)
        .order_by("product_name")
        .values_list("product_name", flat=True)
        .distinct()
    )
    districts = (
        CompanyProductPrice.objects.filter(is_active=True)
        .exclude(district="")
        .order_by("district")
        .values_list("district", flat=True)
        .distinct()
    )

    chart_rows = [
        {
            "company": price.company_name,
            "price": float(price.price_per_unit),
            "unit": price.unit,
            "product": price.product_name,
            "district": price.district or "Not specified",
        }
        for price in prices[:10]
    ]

    product_chart_rows = [
        {
            "product": row["product_name"],
            "average_price": float(row["average_price"] or 0),
            "offers": row["offers"],
        }
        for row in prices.values("product_name")
            .annotate(average_price=Avg("price_per_unit"), offers=Count("id"))
            .order_by("-average_price")[:8]
    ]

    district_chart_rows = [
        {
            "district": row["district"] or "Not specified",
            "average_price": float(row["average_price"] or 0),
            "offers": row["offers"],
        }
        for row in prices.values("district")
            .annotate(average_price=Avg("price_per_unit"), offers=Count("id"))
            .order_by("-average_price")[:8]
    ]

    context = {
        "prices": prices,
        "best_price": best_price,
        "summary": summary,
        "spread_amount": spread_amount,
        "spread_percent": spread_percent,
        "products": products,
        "districts": districts,
        "unit_choices": CompanyProductPrice.UNIT_CHOICES,
        "selected_product": product,
        "selected_district": district,
        "selected_unit": unit,
        "chart_rows": chart_rows,
        "product_chart_rows": product_chart_rows,
        "district_chart_rows": district_chart_rows,
    }
    return render(request, "prices/company_price_compare.html", context)


@login_required
def company_price_create(request):
    form = CompanyProductPriceForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            company_price = form.save(commit=False)
            company_price.entered_by = request.user
            company_price.save()
            messages.success(request, "Company product price added successfully.")
            return redirect("prices:company_price_compare")

    return render(request, "prices/company_price_form.html", {"form": form, "title": "Add Company Price"})
