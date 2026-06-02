from django.shortcuts import redirect, render


def home(request):
    if request.user.is_authenticated:
        return redirect("marketplace:listing_list")
    return render(request, "core/home.html")
