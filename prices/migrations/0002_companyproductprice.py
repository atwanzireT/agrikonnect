# Generated for AgroSync price comparison

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prices", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CompanyProductPrice",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product_name", models.CharField(max_length=120)),
                ("variety", models.CharField(blank=True, max_length=120)),
                ("company_name", models.CharField(max_length=160)),
                ("district", models.CharField(blank=True, max_length=120)),
                ("pickup_location", models.CharField(blank=True, max_length=180)),
                ("unit", models.CharField(choices=[("KG", "Kilogram"), ("BAG", "Bag"), ("TONNE", "Tonne"), ("LITRE", "Litre"), ("TRAY", "Tray"), ("CRATE", "Crate"), ("BUNCH", "Bunch"), ("PIECE", "Piece")], default="KG", max_length=20)),
                ("price_per_unit", models.DecimalField(decimal_places=2, max_digits=12)),
                ("minimum_quantity", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("quality_grade", models.CharField(blank=True, max_length=80)),
                ("payment_terms", models.CharField(blank=True, help_text="Example: Cash on delivery, 7 days, mobile money", max_length=160)),
                ("contact_person", models.CharField(blank=True, max_length=120)),
                ("phone_number", models.CharField(blank=True, max_length=40)),
                ("price_date", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("entered_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="company_product_prices_entered", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["product_name", "-price_per_unit", "company_name"],
                "indexes": [
                    models.Index(fields=["product_name", "district", "is_active"], name="prices_comp_product_c1f6d9_idx"),
                    models.Index(fields=["company_name", "price_date"], name="prices_comp_company_3ba05b_idx"),
                ],
            },
        ),
    ]
