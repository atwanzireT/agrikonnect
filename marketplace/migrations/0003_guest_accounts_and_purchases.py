# Generated for AgroSync guest accounts and marketplace purchases
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0002_marketplace_map_coordinates"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketplacePurchase",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=12)),
                ("unit_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("total_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("delivery_location", models.CharField(blank=True, max_length=255, null=True)),
                ("buyer_phone", models.CharField(blank=True, max_length=20, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="pending", max_length=20)),
                ("buyer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="marketplace_purchases", to=settings.AUTH_USER_MODEL)),
                ("listing", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="purchases", to="marketplace.producelisting")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
