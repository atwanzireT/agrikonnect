from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Count, Sum
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import FarmForm, FarmProjectForm, ProductionBatchForm, HarvestRecordForm, FarmExpenseForm, SalesRecordForm
from .models import Farm, FarmProject, ProductionBatch, HarvestRecord, FarmExpense, SalesRecord, FarmActivity


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
    harvests = HarvestRecord.objects.filter(farmer=request.user).select_related("farm", "project", "batch")
    expenses = FarmExpense.objects.filter(farmer=request.user).select_related("farm", "project", "batch")
    sales = SalesRecord.objects.filter(farmer=request.user).select_related("farm", "project", "batch", "harvest")

    total_farms = farms.count()
    total_harvests = harvests.count()
    projects = FarmProject.objects.filter(farmer=request.user, is_deleted=False).select_related("farm")
    total_projects = projects.count()
    total_acreage = farms.aggregate(total=Sum("acreage")).get("total") or 0
    activity_totals = FarmActivity.objects.filter(farmer=request.user, is_deleted=False).aggregate(labour=Sum("labour_cost"), inputs=Sum("input_cost"))
    total_activity_cost = (activity_totals["labour"] or 0) + (activity_totals["inputs"] or 0)
    total_expenses = expenses.aggregate(total=Sum("amount")).get("total") or 0
    total_sales = sales.aggregate(total=Sum("total_amount")).get("total") or 0
    estimated_profit = total_sales - total_expenses - total_activity_cost

    current_year = timezone.localdate().year
    month_labels = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    current_month_totals = {row["harvest_date__month"]: row["total"] or 0 for row in harvests.filter(harvest_date__year=current_year).values("harvest_date__month").annotate(total=Sum("actual_yield"))}
    last_month_totals = {row["harvest_date__month"]: row["total"] or 0 for row in harvests.filter(harvest_date__year=current_year - 1).values("harvest_date__month").annotate(total=Sum("actual_yield"))}
    max_month_value = max(list(current_month_totals.values()) + list(last_month_totals.values()) + [1])
    production_chart = []
    for month_number, label in enumerate(month_labels, start=1):
        current_value = current_month_totals.get(month_number, 0)
        last_value = last_month_totals.get(month_number, 0)
        production_chart.append({
            "label": label,
            "current": current_value,
            "last": last_value,
            "current_percent": max(3, int((current_value / max_month_value) * 100)) if current_value else 3,
            "last_percent": max(3, int((last_value / max_month_value) * 100)) if last_value else 3,
        })

    project_mix = list(projects.values("project_type").annotate(total=Count("id")).order_by("-total")[:4])
    for item in project_mix:
        item["label"] = dict(FarmProject._meta.get_field("project_type").choices).get(item["project_type"], item["project_type"]).split(" /")[0]
        item["percent"] = round((item["total"] / total_projects) * 100) if total_projects else 0

    top_projects = sorted(list(projects[:50]), key=lambda project: project.actual_revenue or 0, reverse=True)[:5]
    top_farms = farms.annotate(revenue=Sum("sales_records__total_amount")).order_by("-revenue", "farm_name")[:5]

    context = {
        "total_farms": total_farms,
        "total_harvests": total_harvests,
        "total_projects": total_projects,
        "total_acreage": total_acreage,
        "total_activity_cost": total_activity_cost,
        "total_expenses": total_expenses,
        "total_sales": total_sales,
        "estimated_profit": estimated_profit,
        "production_chart": production_chart,
        "project_mix": project_mix,
        "top_projects": top_projects,
        "top_farms": top_farms,
        "recent_farms": farms[:5],
        "recent_projects": projects.order_by("-created_at")[:5],
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
    project_count = FarmProject.objects.filter(farm__in=farms, is_deleted=False).count()
    unique_districts = farms.values('district').distinct().count()
    
    context = {
        'farms': farms,
        'total_acreage': total_acreage,
        'project_count': project_count,
        'unique_districts': unique_districts,
    }
    return render(request, 'farms/farm_list.html', context)


@login_required
def farm_detail(request, pk):
    # Fix: Use request.user directly
    farm = get_object_or_404(Farm, pk=pk, farmer=request.user)

    projects = farm.projects.filter(is_deleted=False).order_by("name")
    batches = farm.production_batches.filter(is_deleted=False).select_related("project").order_by("-start_date", "-created_at")
    harvests = farm.harvest_records.select_related("project").all().order_by("-harvest_date", "-created_at")
    expenses = farm.expenses.select_related("project").all().order_by("-expense_date", "-created_at")
    sales = farm.sales_records.select_related("project", "harvest").all().order_by("-sale_date", "-created_at")

    activity_totals = farm.activities.filter(is_deleted=False).aggregate(labour=Sum("labour_cost"), inputs=Sum("input_cost"))
    total_activity_cost = (activity_totals["labour"] or 0) + (activity_totals["inputs"] or 0)
    total_expenses = expenses.aggregate(total=Sum("amount")).get("total") or 0
    total_sales = sales.aggregate(total=Sum("total_amount")).get("total") or 0
    estimated_profit = total_sales - total_expenses - total_activity_cost

    context = {
        "farm": farm,
        "projects": projects,
        "batches": batches,
        "harvests": harvests,
        "expenses": expenses,
        "sales": sales,
        "total_activity_cost": total_activity_cost,
        "total_expenses": total_expenses,
        "total_sales": total_sales,
        "estimated_profit": estimated_profit,
    }
    return render(request, "farms/farm_detail.html", context)


@login_required
def farm_create(request):
    form = FarmForm(request.POST or None, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                farm = form.save(commit=False)
                farm.farmer = request.user  # Fix: Use request.user directly
                farm.save()
                form.save_projects(farm, request.user)

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
    form = FarmForm(request.POST or None, instance=farm, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            try:
                updated_farm = form.save(commit=False)
                updated_farm.farmer = request.user  # Fix: Use request.user directly
                updated_farm.save()
                form.save_projects(updated_farm, request.user)

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
def project_list(request):
    projects = FarmProject.objects.filter(farmer=request.user, is_deleted=False).select_related("farm").prefetch_related("batches").order_by("farm__farm_name", "name")
    return render(request, "farms/project_list.html", {"projects": projects})


@login_required
def project_create(request, farm_pk=None):
    farm = None
    if farm_pk:
        farm = get_object_or_404(Farm, pk=farm_pk, farmer=request.user)

    form = FarmProjectForm(request.POST or None, farmer=request.user, farm=farm)

    if request.method == "POST":
        if form.is_valid():
            project = form.save(commit=False)
            project.farmer = request.user
            if farm:
                project.farm = farm
            project.save()

            if is_ajax(request):
                return json_success_response(
                    "Farm project added successfully.",
                    extra_data={"project_id": str(project.pk), "farm_id": str(project.farm_id)},
                    status=201,
                )

            messages.success(request, "Farm project added successfully.")
            if farm:
                return redirect("farms:farm_detail", pk=farm.pk)
            return redirect("farms:project_list")

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/project_form.html",
        {
            "form": form,
            "farm": farm,
            "title": "Add Farm Project",
            "submit_label": "Save Project",
        },
    )


@login_required
def project_update(request, pk):
    project = get_object_or_404(FarmProject, pk=pk, farmer=request.user, is_deleted=False)
    form = FarmProjectForm(request.POST or None, instance=project, farmer=request.user)

    if request.method == "POST":
        if form.is_valid():
            updated_project = form.save(commit=False)
            updated_project.farmer = request.user
            updated_project.save()

            if is_ajax(request):
                return json_success_response(
                    "Farm project updated successfully.",
                    extra_data={"project_id": str(updated_project.pk), "farm_id": str(updated_project.farm_id)},
                )

            messages.success(request, "Farm project updated successfully.")
            return redirect("farms:farm_detail", pk=updated_project.farm.pk)

        if is_ajax(request):
            return json_error_response(form.errors, status=400)

    return render(
        request,
        "farms/project_form.html",
        {
            "form": form,
            "project": project,
            "farm": project.farm,
            "title": "Edit Farm Project",
            "submit_label": "Update Project",
        },
    )


@login_required
def batch_list(request):
    batches = ProductionBatch.objects.filter(farmer=request.user, is_deleted=False).select_related("farm", "project").order_by("-start_date", "-created_at")
    return render(request, "farms/batch_list.html", {"batches": batches})


@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(ProductionBatch, pk=pk, farmer=request.user, is_deleted=False)
    context = {
        "batch": batch,
        "activities": batch.activities.filter(is_deleted=False).order_by("-activity_date", "-created_at"),
        "expenses": batch.expenses.filter(is_deleted=False).order_by("-expense_date", "-created_at"),
        "harvests": batch.harvest_records.filter(is_deleted=False).order_by("-harvest_date", "-created_at"),
        "sales": batch.sales_records.filter(is_deleted=False).order_by("-sale_date", "-created_at"),
    }
    return render(request, "farms/batch_detail.html", context)


@login_required
def batch_create(request, project_pk=None):
    project = None
    if project_pk:
        project = get_object_or_404(FarmProject, pk=project_pk, farmer=request.user, is_deleted=False)
    form = ProductionBatchForm(request.POST or None, farmer=request.user, project=project)
    if request.method == "POST":
        if form.is_valid():
            try:
                batch = form.save(commit=False)
                batch.farmer = request.user
                if project:
                    batch.project = project
                    batch.farm = project.farm
                batch.save()
                messages.success(request, "Production batch created successfully.")
                return redirect("farms:batch_detail", pk=batch.pk)
            except (ValidationError, IntegrityError) as e:
                form.add_error(None, e)
    return render(request, "farms/batch_form.html", {"form": form, "project": project, "title": "Add Production Batch", "submit_label": "Save Batch"})


@login_required
def batch_update(request, pk):
    batch = get_object_or_404(ProductionBatch, pk=pk, farmer=request.user, is_deleted=False)
    form = ProductionBatchForm(request.POST or None, instance=batch, farmer=request.user)
    if request.method == "POST":
        if form.is_valid():
            try:
                updated_batch = form.save(commit=False)
                updated_batch.farmer = request.user
                updated_batch.save()
                messages.success(request, "Production batch updated successfully.")
                return redirect("farms:batch_detail", pk=updated_batch.pk)
            except (ValidationError, IntegrityError) as e:
                form.add_error(None, e)
    return render(request, "farms/batch_form.html", {"form": form, "batch": batch, "project": batch.project, "title": "Edit Production Batch", "submit_label": "Update Batch"})


@login_required
def harvest_list(request):
    records = HarvestRecord.objects.filter(farmer=request.user).select_related("farm", "project", "batch").order_by(
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
    expenses = FarmExpense.objects.filter(farmer=request.user).select_related("farm", "project", "batch").order_by(
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
    sales = SalesRecord.objects.filter(farmer=request.user).select_related("farm", "project", "batch", "harvest").order_by(
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


def _money(value):
    return value or Decimal("0")


def _profit_margin(profit, revenue):
    revenue = _money(revenue)
    if revenue <= 0:
        return Decimal("0")
    return (profit / revenue) * Decimal("100")


def _variance_percent(actual, expected):
    expected = _money(expected)
    if expected <= 0:
        return Decimal("0")
    return ((actual - expected) / expected) * Decimal("100")


def _rank_profit_rows(rows):
    if not rows:
        return []
    best_profit = max([row["profit"] for row in rows] + [Decimal("0")])
    for index, row in enumerate(sorted(rows, key=lambda item: item["profit"], reverse=True), start=1):
        row["rank"] = index
        row["profit_margin"] = _profit_margin(row["profit"], row["revenue"])
        row["cost_variance_percent"] = _variance_percent(row["cost"], row.get("expected_cost", 0))
        row["profit_bar_percent"] = 6
        if best_profit > 0 and row["profit"] > 0:
            row["profit_bar_percent"] = max(6, min(100, int((row["profit"] / best_profit) * 100)))
    return rows


@login_required
def profit_compare(request):
    compare = request.GET.get("compare", "projects")
    project_id = request.GET.get("project")
    farm_id = request.GET.get("farm")

    projects = FarmProject.objects.filter(farmer=request.user, is_deleted=False).select_related("farm").order_by("name")
    farms = Farm.objects.filter(farmer=request.user, is_deleted=False).order_by("farm_name")
    selected_project = None
    selected_farm = None
    rows = []

    if compare == "batches":
        batches = ProductionBatch.objects.filter(farmer=request.user, is_deleted=False).select_related("project", "farm")
        if project_id:
            selected_project = get_object_or_404(projects, pk=project_id)
            batches = batches.filter(project=selected_project)
        if farm_id:
            selected_farm = get_object_or_404(farms, pk=farm_id)
            batches = batches.filter(farm=selected_farm)
        for batch in batches:
            rows.append({
                "label": batch.display_name,
                "subtitle": f"{batch.project.name} • {batch.farm.farm_name}",
                "status": batch.get_status_display(),
                "start_date": batch.start_date,
                "expected_revenue": _money(batch.expected_revenue),
                "expected_cost": _money(batch.expected_cost),
                "revenue": _money(batch.actual_revenue),
                "cost": _money(batch.actual_expenses),
                "profit": _money(batch.profit),
                "yield": _money(batch.harvested_quantity),
                "sold_quantity": _money(batch.sold_quantity),
                "url": batch.get_absolute_url() if hasattr(batch, "get_absolute_url") else None,
                "detail_url_name": "farms:batch_detail",
                "pk": batch.pk,
            })
        title = "Batch profit comparison"
        description = "Compare seasons, flocks, ponds, or production cycles against each other."
    elif compare == "farms":
        for farm in farms:
            activity_totals = farm.activities.filter(is_deleted=False).aggregate(labour=Sum("labour_cost"), inputs=Sum("input_cost"))
            activity_cost = _money(activity_totals["labour"]) + _money(activity_totals["inputs"])
            expense_cost = _money(farm.expenses.filter(is_deleted=False).aggregate(total=Sum("amount"))["total"])
            revenue = _money(farm.sales_records.filter(is_deleted=False).aggregate(total=Sum("total_amount"))["total"])
            cost = expense_cost + activity_cost
            rows.append({
                "label": farm.farm_name,
                "subtitle": f"{farm.district}{' • ' + farm.subcounty if farm.subcounty else ''}",
                "status": f"{farm.projects.filter(is_deleted=False).count()} projects",
                "start_date": farm.created_at.date() if farm.created_at else None,
                "expected_revenue": Decimal("0"),
                "expected_cost": Decimal("0"),
                "revenue": revenue,
                "cost": cost,
                "profit": revenue - cost,
                "yield": _money(farm.harvest_records.filter(is_deleted=False).aggregate(total=Sum("actual_yield"))["total"]),
                "sold_quantity": _money(farm.sales_records.filter(is_deleted=False).aggregate(total=Sum("quantity"))["total"]),
                "detail_url_name": "farms:farm_detail",
                "pk": farm.pk,
            })
        title = "Farm profit comparison"
        description = "Compare farm locations to see which one is returning the best profit."
    else:
        compare = "projects"
        if farm_id:
            selected_farm = get_object_or_404(farms, pk=farm_id)
            projects = projects.filter(farm=selected_farm)
        for project in projects:
            rows.append({
                "label": project.name,
                "subtitle": project.farm.farm_name,
                "status": project.get_status_display(),
                "start_date": project.start_date,
                "expected_revenue": _money(project.expected_revenue),
                "expected_cost": _money(project.expected_cost),
                "revenue": _money(project.actual_revenue),
                "cost": _money(project.actual_cost),
                "profit": _money(project.estimated_profit),
                "yield": _money(project.harvest_records.filter(is_deleted=False).aggregate(total=Sum("actual_yield"))["total"]),
                "sold_quantity": _money(project.sales_records.filter(is_deleted=False).aggregate(total=Sum("quantity"))["total"]),
                "detail_url_name": "farms:farm_detail",
                "pk": project.farm.pk,
            })
        title = "Project profit comparison"
        description = "Compare enterprises such as maize, poultry, dairy, fish, coffee, or apiary."

    rows = _rank_profit_rows(rows)
    total_revenue = sum((row["revenue"] for row in rows), Decimal("0"))
    total_cost = sum((row["cost"] for row in rows), Decimal("0"))
    total_profit = total_revenue - total_cost
    best_row = rows[0] if rows else None
    weakest_row = rows[-1] if rows else None

    chart_rows = [
        {
            "label": row["label"],
            "revenue": float(row["revenue"]),
            "cost": float(row["cost"]),
            "profit": float(row["profit"]),
            "margin": float(row["profit_margin"]),
            "yield": float(row["yield"]),
            "sold_quantity": float(row["sold_quantity"]),
        }
        for row in rows[:12]
    ]

    return render(request, "farms/profit_compare.html", {
        "compare": compare,
        "projects": projects if compare != "projects" else FarmProject.objects.filter(farmer=request.user, is_deleted=False).select_related("farm").order_by("name"),
        "farms": farms,
        "selected_project": selected_project,
        "selected_farm": selected_farm,
        "project_id": project_id or "",
        "farm_id": farm_id or "",
        "rows": rows,
        "title": title,
        "description": description,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "overall_margin": _profit_margin(total_profit, total_revenue),
        "best_row": best_row,
        "weakest_row": weakest_row,
        "chart_rows": chart_rows,
    })


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