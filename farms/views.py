from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FarmForm, HarvestRecordForm, FarmExpenseForm, SalesRecordForm
from .models import Farm, HarvestRecord, FarmExpense, SalesRecord


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def json_error_response(errors, status=400):
    return JsonResponse(
        {
            "success": False,
            "errors": errors,
        },
        status=status,
    )


def json_success_response(message, extra_data=None, status=200):
    payload = {
        "success": True,
        "message": message,
    }
    if extra_data:
        payload.update(extra_data)
    return JsonResponse(payload, status=status)


@login_required
def farmer_dashboard(request):
    farms = Farm.objects.filter(farmer=request.user).order_by("-created_at")
    harvests = HarvestRecord.objects.filter(farmer=request.user).select_related("farm")
    expenses = FarmExpense.objects.filter(farmer=request.user).select_related("farm")
    sales = SalesRecord.objects.filter(farmer=request.user).select_related("farm")

    total_farms = farms.count()
    total_harvests = harvests.count()
    total_acreage = farms.aggregate(total=Sum("acreage")).get("total") or 0
    total_expenses = expenses.aggregate(total=Sum("amount")).get("total") or 0
    total_sales = sales.aggregate(total=Sum("total_amount")).get("total") or 0
    estimated_profit = total_sales - total_expenses

    context = {
        "total_farms": total_farms,
        "total_harvests": total_harvests,
        "total_acreage": total_acreage,
        "total_expenses": total_expenses,
        "estimated_profit": estimated_profit,
        "recent_farms": farms[:5],
        "recent_harvests": harvests.order_by("-harvest_date", "-created_at")[:5],
        "recent_expenses": expenses.order_by("-expense_date", "-created_at")[:5],
        "recent_sales": sales.order_by("-sale_date", "-created_at")[:5],
    }
    return render(request, "farms/dashboard.html", context)


@login_required
def farm_list(request):
    # Fix: Use request.user directly instead of request.user.farmer_profile
    farms = Farm.objects.filter(farmer=request.user)
    
    # Calculate additional stats
    total_acreage = farms.aggregate(total=Sum('acreage'))['total'] or 0
    unique_crops = farms.exclude(main_crop__isnull=True).exclude(main_crop='').values('main_crop').distinct().count()
    unique_districts = farms.values('district').distinct().count()
    
    context = {
        'farms': farms,
        'total_acreage': total_acreage,
        'unique_crops': unique_crops,
        'unique_districts': unique_districts,
    }
    return render(request, 'farms/farm_list.html', context)


@login_required
def farm_detail(request, pk):
    # Fix: Use request.user directly
    farm = get_object_or_404(Farm, pk=pk, farmer=request.user)

    harvests = farm.harvest_records.all().order_by("-harvest_date", "-created_at")
    expenses = farm.expenses.all().order_by("-expense_date", "-created_at")
    sales = farm.sales_records.all().order_by("-sale_date", "-created_at")

    total_expenses = expenses.aggregate(total=Sum("amount")).get("total") or 0
    total_sales = sales.aggregate(total=Sum("total_amount")).get("total") or 0
    estimated_profit = total_sales - total_expenses

    context = {
        "farm": farm,
        "harvests": harvests,
        "expenses": expenses,
        "sales": sales,
        "total_expenses": total_expenses,
        "total_sales": total_sales,
        "estimated_profit": estimated_profit,
    }
    return render(request, "farms/farm_detail.html", context)


@login_required
def farm_create(request):
    form = FarmForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            try:
                farm = form.save(commit=False)
                farm.farmer = request.user  # Fix: Use request.user directly
                farm.save()

                if is_ajax(request):
                    return json_success_response(
                        "Farm created successfully.",
                        extra_data={"farm_id": str(farm.pk)},
                        status=201,
                    )

                messages.success(request, "Farm created successfully.")
                return redirect("farms:farm_list")

            except ValidationError as e:
                form.add_error(None, e)

            except IntegrityError:
                form.add_error("farm_name", "You have already recorded this farm.")

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/farm_form.html",
        {
            "form": form,
            "title": "Add Farm",
            "submit_label": "Save Farm",
        },
    )


@login_required
def farm_update(request, pk):
    # Fix: Use request.user directly
    farm = get_object_or_404(Farm, pk=pk, farmer=request.user)
    form = FarmForm(request.POST or None, instance=farm)

    if request.method == "POST":
        if form.is_valid():
            try:
                updated_farm = form.save(commit=False)
                updated_farm.farmer = request.user  # Fix: Use request.user directly
                updated_farm.save()

                if is_ajax(request):
                    return json_success_response(
                        "Farm updated successfully.",
                        extra_data={"farm_id": str(updated_farm.pk)},
                    )

                messages.success(request, "Farm updated successfully.")
                return redirect("farms:farm_list")

            except ValidationError as e:
                form.add_error(None, e)

            except IntegrityError:
                form.add_error("farm_name", "You have already recorded this farm.")

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/farm_form.html",
        {
            "form": form,
            "title": "Edit Farm",
            "submit_label": "Update Farm",
            "farm": farm,
        },
    )


@login_required
def harvest_list(request):
    records = HarvestRecord.objects.filter(farmer=request.user).select_related("farm").order_by(
        "-harvest_date", "-created_at"
    )
    return render(request, "farms/harvest_list.html", {"records": records})


@login_required
def harvest_create(request):
    form = HarvestRecordForm(request.POST or None, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                record = form.save(commit=False)
                record.farmer = request.user
                record.save()

                if is_ajax(request):
                    return json_success_response(
                        "Harvest record added successfully.",
                        extra_data={"record_id": str(record.pk)},
                        status=201,
                    )

                messages.success(request, "Harvest record added successfully.")
                return redirect("farms:harvest_list")

            except ValidationError as e:
                form.add_error(None, e)

            except IntegrityError as e:
                form.add_error(None, str(e))

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/harvest_form.html",
        {
            "form": form,
            "title": "Add Harvest Record",
            "submit_label": "Save Harvest Record",
        },
    )


@login_required
def harvest_update(request, pk):
    record = get_object_or_404(HarvestRecord, pk=pk, farmer=request.user)
    form = HarvestRecordForm(request.POST or None, instance=record, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                updated_record = form.save(commit=False)
                updated_record.farmer = request.user
                updated_record.save()

                if is_ajax(request):
                    return json_success_response(
                        "Harvest record updated successfully.",
                        extra_data={"record_id": str(updated_record.pk)},
                    )

                messages.success(request, "Harvest record updated successfully.")
                return redirect("farms:harvest_list")

            except ValidationError as e:
                form.add_error(None, e)

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/harvest_form.html",
        {
            "form": form,
            "title": "Edit Harvest Record",
            "submit_label": "Update Harvest Record",
            "record": record,
        },
    )


@login_required
def expense_list(request):
    expenses = FarmExpense.objects.filter(farmer=request.user).select_related("farm").order_by(
        "-expense_date", "-created_at"
    )
    
    # Calculate total expenses
    total_expenses = expenses.aggregate(total=Sum("amount")).get("total") or 0
    
    context = {
        "expenses": expenses,
        "total_expenses": total_expenses,
    }
    return render(request, "farms/expense_list.html", context)


@login_required
def expense_create(request):
    form = FarmExpenseForm(request.POST or None, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                expense = form.save(commit=False)
                expense.farmer = request.user
                expense.save()

                if is_ajax(request):
                    return json_success_response(
                        "Expense added successfully.",
                        extra_data={"expense_id": str(expense.pk)},
                        status=201,
                    )

                messages.success(request, "Expense added successfully.")
                return redirect("farms:expense_list")

            except ValidationError as e:
                form.add_error(None, e)

            except IntegrityError as e:
                form.add_error(None, str(e))

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/expense_form.html",
        {
            "form": form,
            "title": "Add Expense",
            "submit_label": "Save Expense",
        },
    )


@login_required
def expense_update(request, pk):
    expense = get_object_or_404(FarmExpense, pk=pk, farmer=request.user)
    form = FarmExpenseForm(request.POST or None, instance=expense, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                updated_expense = form.save(commit=False)
                updated_expense.farmer = request.user
                updated_expense.save()

                if is_ajax(request):
                    return json_success_response(
                        "Expense updated successfully.",
                        extra_data={"expense_id": str(updated_expense.pk)},
                    )

                messages.success(request, "Expense updated successfully.")
                return redirect("farms:expense_list")

            except ValidationError as e:
                form.add_error(None, e)

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/expense_form.html",
        {
            "form": form,
            "title": "Edit Expense",
            "submit_label": "Update Expense",
            "expense": expense,
        },
    )


@login_required
def sale_list(request):
    sales = SalesRecord.objects.filter(farmer=request.user).select_related("farm").order_by(
        "-sale_date", "-created_at"
    )
    
    # Calculate total sales
    total_sales = sales.aggregate(total=Sum("total_amount")).get("total") or 0
    
    context = {
        "sales": sales,
        "total_sales": total_sales,
    }
    return render(request, "farms/sale_list.html", context)


@login_required
def sale_create(request):
    form = SalesRecordForm(request.POST or None, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                sale = form.save(commit=False)
                sale.farmer = request.user
                sale.save()

                if is_ajax(request):
                    return json_success_response(
                        "Sale record added successfully.",
                        extra_data={"sale_id": str(sale.pk), "total_amount": str(sale.total_amount)},
                        status=201,
                    )

                messages.success(request, "Sale record added successfully.")
                return redirect("farms:sale_list")

            except ValidationError as e:
                form.add_error(None, e)

            except IntegrityError as e:
                form.add_error(None, str(e))

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/sale_form.html",
        {
            "form": form,
            "title": "Add Sale Record",
            "submit_label": "Save Sale Record",
        },
    )


@login_required
def sale_update(request, pk):
    sale = get_object_or_404(SalesRecord, pk=pk, farmer=request.user)
    form = SalesRecordForm(request.POST or None, instance=sale, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                updated_sale = form.save(commit=False)
                updated_sale.farmer = request.user
                updated_sale.save()

                if is_ajax(request):
                    return json_success_response(
                        "Sale record updated successfully.",
                        extra_data={"sale_id": str(updated_sale.pk), "total_amount": str(updated_sale.total_amount)},
                    )

                messages.success(request, "Sale record updated successfully.")
                return redirect("farms:sale_list")

            except ValidationError as e:
                form.add_error(None, e)

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/sale_form.html",
        {
            "form": form,
            "title": "Edit Sale Record",
            "submit_label": "Update Sale Record",
            "sale": sale,
        },
    )


@login_required
def profit_summary(request):
    farms = Farm.objects.filter(farmer=request.user)
    expenses = FarmExpense.objects.filter(farmer=request.user)
    sales = SalesRecord.objects.filter(farmer=request.user)

    total_farms = farms.count()
    total_acreage = farms.aggregate(total=Sum("acreage")).get("total") or 0
    total_expenses = expenses.aggregate(total=Sum("amount")).get("total") or 0
    total_sales = sales.aggregate(total=Sum("total_amount")).get("total") or 0
    estimated_profit = total_sales - total_expenses

    # Calculate profit margin
    profit_margin = 0
    if total_sales > 0:
        profit_margin = (estimated_profit / total_sales) * 100

    context = {
        "total_farms": total_farms,
        "total_acreage": total_acreage,
        "total_expenses": total_expenses,
        "total_sales": total_sales,
        "estimated_profit": estimated_profit,
        "profit_margin": profit_margin,
    }
    return render(request, "farms/profit_summary.html", context)