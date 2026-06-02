# Generated for AgroSync farmer mobile/offline API upgrade

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("farms", "0002_farm_unique_farm_per_farmer_location"),
    ]

    operations = [
        migrations.AddField("farm", "client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
        migrations.AddField("farm", "client_updated_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("farm", "sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
        migrations.AddField("farm", "is_deleted", models.BooleanField(db_index=True, default=False)),
        migrations.AddField("harvestrecord", "client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
        migrations.AddField("harvestrecord", "client_updated_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("harvestrecord", "sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
        migrations.AddField("harvestrecord", "is_deleted", models.BooleanField(db_index=True, default=False)),
        migrations.AddField("farmexpense", "client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
        migrations.AddField("farmexpense", "client_updated_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("farmexpense", "sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
        migrations.AddField("farmexpense", "is_deleted", models.BooleanField(db_index=True, default=False)),
        migrations.AddField("salesrecord", "client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
        migrations.AddField("salesrecord", "client_updated_at", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("salesrecord", "sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
        migrations.AddField("salesrecord", "is_deleted", models.BooleanField(db_index=True, default=False)),
        migrations.CreateModel(
            name="FarmActivity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client_id", models.CharField(blank=True, db_index=True, max_length=80, null=True)),
                ("client_updated_at", models.DateTimeField(blank=True, null=True)),
                ("sync_status", models.CharField(choices=[("synced", "Synced"), ("pending", "Pending"), ("conflict", "Conflict")], db_index=True, default="synced", max_length=20)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("activity_type", models.CharField(choices=[("land_preparation", "Land preparation"), ("planting", "Planting"), ("weeding", "Weeding"), ("fertilizer", "Fertilizer application"), ("spraying", "Spraying"), ("irrigation", "Irrigation"), ("pruning", "Pruning"), ("harvesting", "Harvesting"), ("post_harvest", "Post-harvest"), ("other", "Other")], default="other", max_length=40)),
                ("title", models.CharField(max_length=150)),
                ("activity_date", models.DateField()),
                ("crop_name", models.CharField(blank=True, max_length=100, null=True)),
                ("labour_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("input_cost", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("notes", models.TextField(blank=True, null=True)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="farms.farm")),
                ("farmer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="farm_activities", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-activity_date", "-created_at"],
                "indexes": [models.Index(fields=["farmer", "activity_date"], name="farms_farma_farmer__664975_idx"), models.Index(fields=["farmer", "updated_at"], name="farms_farma_farmer__a4fe11_idx")],
            },
        ),
        migrations.AddConstraint("farm", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_farm_client_id")),
        migrations.AddConstraint("harvestrecord", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_harvest_client_id")),
        migrations.AddConstraint("farmexpense", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_expense_client_id")),
        migrations.AddConstraint("salesrecord", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_sale_client_id")),
        migrations.AddConstraint("farmactivity", models.UniqueConstraint(fields=("farmer", "client_id"), condition=models.Q(("client_id__isnull", False)), name="unique_farmer_activity_client_id")),
    ]
