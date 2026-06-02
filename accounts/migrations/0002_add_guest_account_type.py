# Generated for AgroSync guest accounts
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="account_type",
            field=models.CharField(choices=[("farmer", "Farmer"), ("business", "Business"), ("guest", "Guest"), ("admin", "Admin")], max_length=20),
        ),
    ]
