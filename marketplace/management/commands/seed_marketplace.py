from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from marketplace.models import ProduceListing, BuyerRequest
from farms.models import Farm
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed marketplace sample products"

    def handle(self, *args, **kwargs):

        farmers = User.objects.filter(account_type="farmer")[:5]

        if not farmers.exists():
            self.stdout.write(
                self.style.ERROR(
                    "Create farmer accounts first."
                )
            )
            return

        products = [
            {
                "crop_name": "Robusta Coffee",
                "variety": "FAQ",
                "quantity": 1200,
                "price": 12800,
                "district": "Kasese",
                "lat": 0.1833,
                "lon": 30.0833,
            },
            {
                "crop_name": "Arabica Coffee",
                "variety": "Bugisu",
                "quantity": 700,
                "price": 15500,
                "district": "Mbale",
                "lat": 1.0820,
                "lon": 34.1750,
            },
            {
                "crop_name": "Maize",
                "variety": "Longe 10",
                "quantity": 2500,
                "price": 1700,
                "district": "Kasese",
                "lat": 0.1690,
                "lon": 30.0780,
            },
            {
                "crop_name": "Beans",
                "variety": "NABE 15",
                "quantity": 950,
                "price": 3800,
                "district": "Fort Portal",
                "lat": 0.6617,
                "lon": 30.2748,
            },
            {
                "crop_name": "Vanilla",
                "variety": "Premium",
                "quantity": 120,
                "price": 28000,
                "district": "Bundibugyo",
                "lat": 0.7124,
                "lon": 30.0644,
            },
            {
                "crop_name": "Cocoa",
                "variety": "Dry Beans",
                "quantity": 650,
                "price": 9400,
                "district": "Bundibugyo",
                "lat": 0.7110,
                "lon": 30.0620,
            },
            {
                "crop_name": "Rice",
                "variety": "Super",
                "quantity": 1800,
                "price": 4200,
                "district": "Hoima",
                "lat": 1.4331,
                "lon": 31.3524,
            },
        ]

        for item in products:

            farmer = random.choice(farmers)

            farm = Farm.objects.filter(
                farmer=farmer
            ).first()

            if not farm:
                continue

            ProduceListing.objects.create(
                farm=farm,
                farmer=farmer,
                crop_name=item["crop_name"],
                variety=item["variety"],
                quantity=item["quantity"],
                unit="kg",
                expected_price=item["price"],
                district=item["district"],
                latitude=item["lat"],
                longitude=item["lon"],
                status="open",
                description=f"{item['crop_name']} available for sale",
            )

        businesses = User.objects.filter(
            account_type="business"
        )[:3]

        requests = [
            ("Robusta Coffee", 5000, 12000, 13500),
            ("Maize", 3000, 1500, 2000),
            ("Beans", 1500, 3500, 4200),
            ("Cocoa", 800, 9000, 10000),
        ]

        for business in businesses:

            for crop, qty, low, high in requests:

                BuyerRequest.objects.create(
                    business_user=business,
                    crop_name=crop,
                    quantity_needed=qty,
                    unit="kg",
                    min_price=low,
                    max_price=high,
                    delivery_district="Kampala",
                    delivery_location="Industrial Area",
                    latitude=0.3476,
                    longitude=32.5825,
                    status="open",
                    notes=f"Looking for {crop}",
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Marketplace sample data created."
            )
        )