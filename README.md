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
