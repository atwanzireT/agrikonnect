# AgriKonnect Farmer Mobile Login Fix

This adjusted Django project allows the farmer Flutter app to log in using the same credentials as the web version.

## Supported login fields

`POST /api/farmers/login/` accepts any of these request bodies:

```json
{
  "identifier": "farmer@email.com",
  "password": "password"
}
```

```json
{
  "identifier": "0771234567",
  "password": "password"
}
```

Older mobile builds are also supported if they send `username`, `phone_or_email`, `phone`, or `email`.

## Phone formats supported

The API accepts common Uganda phone formats and matches them against the saved user phone:

- `0771234567`
- `256771234567`
- `+256771234567`
- `771234567`

## Development server

Run Django like this so the phone can access it:

```bash
python manage.py runserver 0.0.0.0:8000
```

In Flutter, set the base URL to your computer IP, for example:

```dart
static const baseUrl = "http://192.168.1.137:8000";
```

## Host settings

For development, this project now reads:

```python
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
```

For production, set `ALLOWED_HOSTS` in `.env`, for example:

```env
ALLOWED_HOSTS=agrikonnect.com,www.agrikonnect.com
```
