# Manual migration: link farm records to farm projects and support project acreage.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("farms", "0006_remove_farmproject_unique_farmer_project_client_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="farmproject",
            name="acreage",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name="farmproject",
            name="project_type",
            field=models.CharField(
                choices=[
                    ("crop", "Crop production"),
                    ("livestock", "Livestock"),
                    ("poultry", "Poultry"),
                    ("dairy", "Dairy"),
                    ("cattle", "Cattle"),
                    ("goats", "Goats"),
                    ("piggery", "Piggery"),
                    ("fish", "Fish farming"),
                    ("beekeeping", "Beekeeping / Apiary"),
                    ("horticulture", "Horticulture"),
                    ("forestry", "Forestry"),
                    ("other", "Other"),
                ],
                db_index=True,
                default="crop",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="farmactivity",
            name="project",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="activities", to="farms.farmproject"),
        ),
        migrations.AddField(
            model_name="farmexpense",
            name="project",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expenses", to="farms.farmproject"),
        ),
        migrations.AddField(
            model_name="harvestrecord",
            name="project",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="harvest_records", to="farms.farmproject"),
        ),
        migrations.AddField(
            model_name="salesrecord",
            name="project",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sales_records", to="farms.farmproject"),
        ),
        migrations.AddField(
            model_name="salesrecord",
            name="harvest",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sales_records", to="farms.harvestrecord"),
        ),
    ]
