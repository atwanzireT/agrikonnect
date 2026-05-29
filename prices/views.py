from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import MarketPriceForm
from .models import MarketPrice


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