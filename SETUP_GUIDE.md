# AgriKonnect Farmer Mobile App Setup

This Flutter app is farmer-only and connects to the adjusted Django backend.

## 1. Extract the ZIP
Open the extracted folder in VS Code or terminal.

## 2. Generate platform files
Run this inside the project folder:

```bash
flutter create .
```

## 3. Confirm Android internet permission
Open `android/app/src/main/AndroidManifest.xml` and make sure this line is above `<application>`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

## 4. Set backend URL
Open:

`lib/utils/constants.dart`

Set your computer/server IP:

```dart
static const String baseUrl = 'http://192.168.1.137:8000';
```

## 5. Run Django
On the Django project:

```bash
python manage.py runserver 0.0.0.0:8000
```

In Django `settings.py`, for development:

```python
ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True
```

## 6. Run Flutter

```bash
flutter clean
flutter pub get
flutter run
```

## Login payload
The app sends all compatible fields to `/api/farmers/login/`:

```json
{
  "identifier": "username/email/phone",
  "username": "username/email/phone",
  "phone_or_email": "username/email/phone",
  "password": "password"
}
```

## Included farmer modules
- Login using web credentials
- Password show/hide
- Dashboard
- Farms
- Activities
- Expenses
- Harvests
- Sales
- Marketplace listings
- Buyer requests
- Offline SQLite queue and sync support
