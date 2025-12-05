from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "STTE Ekupoint Admin"
admin.site.site_title = "STTE Ekupoint Admin Portal"
admin.site.index_title = "Site Administration for STTE Ekupoint"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('contacts.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)