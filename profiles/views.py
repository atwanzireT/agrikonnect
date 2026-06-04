from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    FarmerProfileForm,
    BusinessProfileForm,
    BusinessVerificationDocumentForm,
)
from .models import FarmerProfile, BusinessProfile


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def form_errors(form):
    return {
        field: [str(error) for error in errors]
        for field, errors in form.errors.items()
    }


@login_required
def farmer_profile_update(request):
    profile, _ = FarmerProfile.objects.get_or_create(user=request.user)
    form = FarmerProfileForm(request.POST or None, instance=profile)

    if request.method == "POST":
        if form.is_valid():
            form.save()

            if is_ajax(request):
                return JsonResponse({
                    "success": True,
                    "message": "Profile updated successfully.",
                })

            messages.success(request, "Profile updated successfully.")
            return redirect("profiles:farmer_profile_update")

        if is_ajax(request):
            return JsonResponse({
                "success": False,
                "message": "Please correct the highlighted errors.",
                "errors": form_errors(form),
            }, status=400)

    return render(
        request,
        "profiles/farmer_profile_form.html",
        {
            "form": form,
            "profile": profile,
        }
    )


@login_required
def business_profile_update(request):
    profile, _ = BusinessProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "business_name": request.user.full_name,
            "contact_person": request.user.full_name,
            "district": request.user.district,
        }
    )

    form = BusinessProfileForm(request.POST or None, instance=profile)

    if request.method == "POST":
        if form.is_valid():
            business = form.save(commit=False)
            business.user = request.user
            business.save()

            if is_ajax(request):
                return JsonResponse({
                    "success": True,
                    "message": "Business profile updated successfully.",
                })

            messages.success(request, "Business profile updated successfully.")
            return redirect("profiles:business_profile_update")

        if is_ajax(request):
            return JsonResponse({
                "success": False,
                "message": "Please correct the highlighted errors.",
                "errors": form_errors(form),
            }, status=400)

    return render(
        request,
        "profiles/business_profile_form.html",
        {
            "form": form,
            "profile": profile,
        }
    )


@login_required
def business_document_upload(request):
    profile, _ = BusinessProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "business_name": request.user.full_name,
            "contact_person": request.user.full_name,
            "district": request.user.district,
        }
    )

    form = BusinessVerificationDocumentForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST":
        if form.is_valid():
            document = form.save(commit=False)
            document.business_profile = profile
            document.save()

            if is_ajax(request):
                return JsonResponse({
                    "success": True,
                    "message": "Document uploaded successfully.",
                    "redirect_url": "/profiles/business/",
                })

            messages.success(request, "Document uploaded successfully.")
            return redirect("profiles:business_profile_update")

        if is_ajax(request):
            return JsonResponse({
                "success": False,
                "message": "Please correct the highlighted errors.",
                "errors": form_errors(form),
            }, status=400)

    return render(
        request,
        "profiles/business_document_upload.html",
        {
            "form": form,
            "profile": profile,
        }
    )