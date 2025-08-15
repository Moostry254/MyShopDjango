# myshop/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Keep only this line if you want your shop to be the homepage
    path('', include('shop.urls')),
    # Remove or comment out the line below:
    # path('products/', include('shop.urls')),
]

# Serve static and media files during development (ONLY for DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)