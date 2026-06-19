# Manual migration: introduce production batches/seasons and link farm records to batches.

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("farms", "0007_project_linked_farm_records"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductionBatch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
                ("client_updated_at", models.DateTimeField(blank=True, null=True)),
                ("sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("batch_code", models.CharField(db_index=True, max_length=80)),
                ("name", models.CharField(blank=True, max_length=160, null=True)),
                ("season", models.CharField(blank=True, max_length=100, null=True)),
                ("start_date", models.DateField()),
                ("expected_end_date", models.DateField(blank=True, null=True)),
                ("actual_end_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("planned", "Planned"), ("active", "Active"), ("harvested", "Harvested"), ("sold_out", "Sold out"), ("closed", "Closed"), ("cancelled", "Cancelled")], db_index=True, default="planned", max_length=20)),
                ("area_or_units", models.DecimalField(blank=True, decimal_places=2, help_text="Acres, birds, animals, ponds, beds, or other production units.", max_digits=12, null=True)),
                ("unit_label", models.CharField(default="acre", max_length=30)),
                ("expected_quantity", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("expected_unit", models.CharField(default="kg", max_length=20)),
                ("expected_revenue", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("expected_cost", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("notes", models.TextField(blank=True, null=True)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="production_batches", to="farms.farm")),
                ("farmer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="production_batches", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="farms.farmproject")),
            ],
            options={
                "ordering": ["-start_date", "-created_at"],
                "indexes": [models.Index(fields=["farmer", "status"], name="farms_produ_farmer__98df3a_idx"), models.Index(fields=["project", "start_date"], name="farms_produ_project_39b92f_idx")],
            },
        ),
        migrations.AddConstraint(
            model_name="productionbatch",
            constraint=models.UniqueConstraint(fields=("project", "batch_code"), name="unique_batch_code_per_project"),
        ),
        migrations.AddField(
            model_name="farmactivity",
            name="batch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activities", to="farms.productionbatch"),
        ),
        migrations.AddField(
            model_name="farmexpense",
            name="batch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expenses", to="farms.productionbatch"),
        ),
        migrations.AddField(
            model_name="harvestrecord",
            name="batch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="harvest_records", to="farms.productionbatch"),
        ),
        migrations.AddField(
            model_name="salesrecord",
            name="batch",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sales_records", to="farms.productionbatch"),
        ),
    ]
