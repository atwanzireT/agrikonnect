# Generated for AgriKonnect project planner and profit tracking upgrade

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("farms", "0003_offline_sync_and_farmactivity"),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmProject",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
                ("client_updated_at", models.DateTimeField(blank=True, null=True)),
                ("sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("name", models.CharField(max_length=160)),
                ("project_type", models.CharField(choices=[("crop", "Crop production"), ("poultry", "Poultry"), ("cattle", "Cattle"), ("goats", "Goats"), ("piggery", "Piggery"), ("fish", "Fish farming"), ("beekeeping", "Beekeeping"), ("other", "Other")], db_index=True, default="crop", max_length=30)),
                ("description", models.TextField(blank=True, null=True)),
                ("start_date", models.DateField()),
                ("expected_end_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("planned", "Planned"), ("active", "Active"), ("paused", "Paused"), ("completed", "Completed"), ("cancelled", "Cancelled")], db_index=True, default="planned", max_length=20)),
                ("expected_revenue", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("expected_cost", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("target_quantity", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("target_unit", models.CharField(default="kg", max_length=20)),
                ("notes", models.TextField(blank=True, null=True)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="farms.farm")),
                ("farmer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="farm_projects", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-start_date", "-created_at"],
                "indexes": [
                    models.Index(fields=["farmer", "status"], name="farms_farmpr_farmer__status_idx"),
                    models.Index(fields=["farmer", "project_type"], name="farms_farmpr_farmer__ptype_idx"),
                    models.Index(fields=["farmer", "updated_at"], name="farms_farmpr_farmer__upd_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ProjectPlannedActivity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
                ("client_updated_at", models.DateTimeField(blank=True, null=True)),
                ("sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("title", models.CharField(max_length=160)),
                ("activity_type", models.CharField(choices=[("land_preparation", "Land preparation"), ("planting", "Planting"), ("weeding", "Weeding"), ("fertilizer", "Fertilizer application"), ("spraying", "Spraying"), ("irrigation", "Irrigation"), ("pruning", "Pruning"), ("harvesting", "Harvesting"), ("post_harvest", "Post-harvest"), ("other", "Other")], default="other", max_length=40)),
                ("planned_date", models.DateField()),
                ("completed_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("todo", "To do"), ("in_progress", "In progress"), ("done", "Done"), ("missed", "Missed"), ("cancelled", "Cancelled")], db_index=True, default="todo", max_length=20)),
                ("estimated_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("actual_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("assigned_to", models.CharField(blank=True, max_length=120, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_plans", to="farms.farm")),
                ("farmer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_planned_activities", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="planned_activities", to="farms.farmproject")),
            ],
            options={
                "ordering": ["planned_date", "created_at"],
                "indexes": [
                    models.Index(fields=["farmer", "planned_date"], name="farms_projpl_farmer__date_idx"),
                    models.Index(fields=["project", "status"], name="farms_projpl_project_status_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ProjectInputRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
                ("client_updated_at", models.DateTimeField(blank=True, null=True)),
                ("sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("category", models.CharField(choices=[("feeds", "Feeds"), ("drugs", "Drugs / veterinary"), ("labour", "Labour"), ("seed", "Seed / seedlings"), ("fertilizer", "Fertilizer"), ("chemicals", "Chemicals"), ("transport", "Transport"), ("equipment", "Equipment"), ("other", "Other")], db_index=True, default="other", max_length=30)),
                ("item_name", models.CharField(max_length=160)),
                ("quantity", models.DecimalField(decimal_places=2, default=1, max_digits=12)),
                ("unit", models.CharField(default="unit", max_length=20)),
                ("unit_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("total_cost", models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=14)),
                ("record_date", models.DateField(db_index=True)),
                ("supplier_name", models.CharField(blank=True, max_length=160, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_inputs", to="farms.farm")),
                ("farmer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_input_records", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="input_records", to="farms.farmproject")),
            ],
            options={
                "ordering": ["-record_date", "-created_at"],
                "indexes": [
                    models.Index(fields=["farmer", "category"], name="farms_projinput_farmer_cat_idx"),
                    models.Index(fields=["project", "record_date"], name="farms_projinput_project_date_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ProjectRevenueRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
                ("client_updated_at", models.DateTimeField(blank=True, null=True)),
                ("sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("description", models.CharField(max_length=180)),
                ("quantity", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("unit", models.CharField(default="unit", max_length=20)),
                ("price_per_unit", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("amount", models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=14)),
                ("revenue_date", models.DateField(db_index=True)),
                ("buyer_name", models.CharField(blank=True, max_length=160, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_revenues", to="farms.farm")),
                ("farmer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_revenue_records", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="revenue_records", to="farms.farmproject")),
            ],
            options={
                "ordering": ["-revenue_date", "-created_at"],
                "indexes": [models.Index(fields=["project", "revenue_date"], name="farms_projrev_project_date_idx")],
            },
        ),
        migrations.AddConstraint("farmproject", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_project_client_id")),
        migrations.AddConstraint("projectplannedactivity", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_plan_client_id")),
        migrations.AddConstraint("projectinputrecord", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_input_client_id")),
        migrations.AddConstraint("projectrevenuerecord", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_revenue_client_id")),
    ]
