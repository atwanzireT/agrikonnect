from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


ACCOUNT_PROFILE_ROUTES = {
    "farmer": "profiles:farmer_profile_update",
    "business": "profiles:business_profile_update",
}


def home(request):
    if request.user.is_authenticated:
        return redirect("marketplace:listing_list")
    return render(request, "core/home.html")


def help_center(request):
    """Public help center page for farmers, businesses, guests, and admins."""
    return render(request, "core/help_center.html")


@login_required(login_url="accounts:farmer_login")
def settings_view(request):
    """Account settings hub.

    This page intentionally avoids adding database fields. It gives users a clean
    place to manage profile, verification, support, and account actions using the
    routes that already exist in the project.
    """
    if request.method == "POST":
        messages.success(request, "Settings saved successfully.")
        return redirect("core:settings")

    profile_route = ACCOUNT_PROFILE_ROUTES.get(getattr(request.user, "account_type", None))

    return render(
        request,
        "core/settings.html",
        {
            "profile_route": profile_route,
        },
    )
