# agrikonnect/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
    path('profiles/', include('profiles.urls')),

    # FIX THIS LINE
    path('farms/', include(('farms.urls', 'farms'), namespace='farms')),

    path('marketplace/', include('marketplace.urls')),
    path('prices/', include('prices.urls')),

    # API URLs
    path("api/farmers/", include("farmers_api.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
