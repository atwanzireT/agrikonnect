from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ProduceListingForm, BuyerRequestForm, ListingInquiryForm, ProduceListingImageForm, MarketplacePurchaseForm
from .models import (
    ProduceListing,
    ProduceListingImage,
    ListingInquiry,
    BuyerRequest,
    BuyerRequestImage,
    MarketplacePurchase,
)


def _save_listing_images(listing, user, files):
    """Attach uploaded product images and make the first image primary when needed."""
    existing_primary = listing.images.filter(is_primary=True).exists()
    base_order = listing.images.count()
    for index, image in enumerate(files):
        ProduceListingImage.objects.create(
            listing=listing,
            uploaded_by=user,
            image=image,
            is_primary=(not existing_primary and index == 0),
            sort_order=base_order + index,
        )


@login_required
def business_dashboard(request):
    recent_demands = BuyerRequest.objects.filter(
        business_user=request.user
    ).order_by("-created_at")[:5]

    active_demands = BuyerRequest.objects.filter(
        business_user=request.user,
        status="open"
    ).count()

    farmer_offers = ProduceListing.objects.filter(status="open").count()

    suggested_matches = ProduceListing.objects.filter(
        status="open"
    ).order_by("-created_at")[:5]

    avg_market_price = ProduceListing.objects.aggregate(
        avg_price=Avg("expected_price")
    )["avg_price"] or 0

    context = {
        "recent_demands": recent_demands,
        "active_demands": active_demands,
        "farmer_offers": farmer_offers,
        "nearby_matches": suggested_matches.count(),
        "avg_market_price": round(avg_market_price),
        "suggested_matches": suggested_matches,
    }

    return render(request, "marketplace/business_dashboard.html", context)


@login_required
def listing_list(request):
    listings = ProduceListing.objects.filter(status="open").order_by("-created_at")

    search = request.GET.get("q")
    location = request.GET.get("location")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if search:
        listings = listings.filter(
            Q(crop_name__icontains=search) |
            Q(variety__icontains=search) |
            Q(description__icontains=search)
        )

    if location:
        listings = listings.filter(
            Q(district__icontains=location) |
            Q(subcounty__icontains=location) |
            Q(village__icontains=location)
        )

    if min_price:
        listings = listings.filter(expected_price__gte=min_price)

    if max_price:
        listings = listings.filter(expected_price__lte=max_price)

    return render(request, "marketplace/listing_list.html", {"listings": listings})


@login_required
def listing_detail(request, pk):
    listing = get_object_or_404(ProduceListing, pk=pk)
    context = {
        "listing": listing,
        "inquiry_form": ListingInquiryForm(),
        "image_form": ProduceListingImageForm(),
        "purchase_form": MarketplacePurchaseForm(initial={"quantity": 1}),
    }
    return render(request, "marketplace/listing_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def listing_create(request):
    if getattr(request.user, "account_type", None) == "guest":
        messages.error(request, "Guest accounts can buy products but cannot create listings.")
        return redirect("marketplace:listing_list")

    if request.method == "POST":
        form = ProduceListingForm(request.POST, farmer=request.user)

        if form.is_valid():
            listing = form.save(commit=False)
            listing.farmer = request.user
            listing.save()

            _save_listing_images(listing, request.user, request.FILES.getlist("images"))

            messages.success(request, "Product listing created successfully with its description and images.")
            return redirect("marketplace:listing_detail", pk=listing.pk)
    else:
        form = ProduceListingForm(farmer=request.user)

    return render(request, "marketplace/listing_form.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def listing_image_upload(request, pk):
    listing = get_object_or_404(ProduceListing, pk=pk, farmer=request.user)

    if request.method == "POST":
        images = request.FILES.getlist("images")

        if not images:
            messages.error(request, "Please select at least one image.")
            return redirect("marketplace:listing_image_upload", pk=listing.pk)

        _save_listing_images(listing, request.user, images)

        messages.success(request, "Images uploaded successfully.")
        return redirect("marketplace:listing_detail", pk=listing.pk)

    return render(request, "marketplace/listing_image_upload.html", {"listing": listing})


@login_required
@require_http_methods(["POST"])
def inquiry_create(request, pk):
    listing = get_object_or_404(ProduceListing, pk=pk)

    ListingInquiry.objects.create(
        listing=listing,
        business_user=request.user,
        message=request.POST.get("message", ""),
    )

    messages.success(request, "Inquiry submitted successfully.")
    return redirect("marketplace:listing_detail", pk=listing.pk)


@login_required
@require_http_methods(["POST"])
def purchase_create(request, pk):
    listing = get_object_or_404(ProduceListing, pk=pk, status="open")
    form = MarketplacePurchaseForm(request.POST)
    if form.is_valid():
        purchase = form.save(commit=False)
        purchase.listing = listing
        purchase.buyer = request.user
        purchase.unit_price = listing.expected_price
        purchase.save()
        messages.success(request, "Purchase request submitted successfully. The seller will contact you.")
        return redirect("marketplace:listing_detail", pk=listing.pk)
    messages.error(request, "Please correct the purchase details and try again.")
    return render(request, "marketplace/listing_detail.html", {
        "listing": listing,
        "inquiry_form": ListingInquiryForm(),
        "image_form": ProduceListingImageForm(),
        "purchase_form": form,
    })


@login_required
def buyer_request_list(request):
    requests = BuyerRequest.objects.order_by("-created_at")

    search = request.GET.get("q")
    location = request.GET.get("location")

    if search:
        requests = requests.filter(
            Q(crop_name__icontains=search) |
            Q(variety__icontains=search) |
            Q(notes__icontains=search)
        )

    if location:
        requests = requests.filter(
            Q(delivery_district__icontains=location) |
            Q(delivery_location__icontains=location)
        )

    return render(request, "marketplace/buyer_request_list.html", {"requests": requests})


@login_required
@require_http_methods(["GET", "POST"])
def buyer_request_create(request):
    if request.method == "POST":
        form = BuyerRequestForm(request.POST)

        if form.is_valid():
            buyer_request = form.save(commit=False)
            buyer_request.business_user = request.user
            buyer_request.save()

            for image in request.FILES.getlist("images"):
                BuyerRequestImage.objects.create(
                    buyer_request=buyer_request,
                    uploaded_by=request.user,
                    image=image,
                )

            messages.success(request, "Buying request posted successfully.")
            return redirect("marketplace:buyer_request_list")
    else:
        form = BuyerRequestForm()

    return render(request, "marketplace/buyer_request_form.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def buyer_request_image_upload(request, pk):
    buyer_request = get_object_or_404(
        BuyerRequest,
        pk=pk,
        business_user=request.user,
    )

    if request.method == "POST":
        images = request.FILES.getlist("images")

        if not images:
            messages.error(request, "Please select images.")
            return redirect("marketplace:buyer_request_image_upload", pk=buyer_request.pk)

        for image in images:
            BuyerRequestImage.objects.create(
                buyer_request=buyer_request,
                uploaded_by=request.user,
                image=image,
            )

        messages.success(request, "Images uploaded successfully.")
        return redirect("marketplace:buyer_request_list")

    return render(
        request,
        "marketplace/buyer_request_image_upload.html",
        {"buyer_request": buyer_request},
    )


@login_required
def market_map(request):
    farmer_pins = ProduceListing.objects.filter(
        status="open",
        latitude__isnull=False,
        longitude__isnull=False,
    )

    buyer_pins = BuyerRequest.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    )

    return render(
        request,
        "marketplace/market_map.html",
        {
            "farmer_pins": farmer_pins,
            "buyer_pins": buyer_pins,
        },
    )


@login_required
def price_list(request):
    listings = ProduceListing.objects.filter(status="open").order_by("-created_at")
    return render(request, "marketplace/price_list.html", {"listings": listings})