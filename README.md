# Agrikonnect Recreated

Cleaned Django project with shared farmer registration for web portal and mobile API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install django djangorestframework python-dotenv pillow
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Farmer account creation

Web portal:

```text
/accounts/farmer/request-otp/
/accounts/farmer/signup/
```

Mobile API:

```text
POST /api/farmers/register/
```

Example payload:

```json
{
  "full_name": "Test Farmer",
  "phone": "0771234567",
  "password": "123456",
  "district": "Kampala",
  "account_type": "farmer"
}
```

Android emulator base URL:

```text
http://10.0.2.2:8000
```

Real phone base URL: use your computer LAN IP, for example:

```text
http://192.168.1.137:8000
```

## Batch-based farm records update

This rebuild adds production batches below farm projects so records stay clean across seasons and production cycles.

New structure:

```text
Farm
  -> Project, e.g. Maize, Broilers, Fish Pond
      -> Production Batch, e.g. 2026A, Flock 001, Pond Cycle 01
          -> Activities
          -> Expenses
          -> Harvests
          -> Sales
```

Key additions:

- `ProductionBatch` model with batch code, season, status, start/end dates, area/units, expected output, expected cost, and expected revenue.
- Harvest, expense, sales, and activity records now support a `batch` foreign key.
- Batch dashboard pages show batch revenue, expenses, profit, harvested quantity, sold quantity, and stock balance.
- Web routes added under `/farms/batches/`.
- API route added under `/api/batches/` with a batch profit summary action.

After updating your environment, run:

```bash
python manage.py migrate
```

Note: Django was not installed in the rebuild container, so migrations were written manually and Python syntax was checked with `py_compile`.
