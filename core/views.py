from django.shortcuts import render


def home(request):
    if request.user.is_authenticated:
        user = request.user
        dashboard_url = "/"

        if user.account_type == "farmer":
            dashboard_url = "/farms/dashboard/"
        elif user.account_type == "business":
            dashboard_url = "/marketplace/business/dashboard/"
        elif user.is_superuser or user.account_type == "admin":
            dashboard_url = "/admin/"

        return render(request, "core/home.html", {
            "dashboard_url": dashboard_url,
        })

    return render(request, "core/home.html")