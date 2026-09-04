from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

API_V1 = "api/v1/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(API_V1 + "auth/", include("apps.accounts.urls")),
    path(API_V1 + "tasks/", include("apps.tasks.urls")),
    path(API_V1 + "lists/", include("apps.lists.urls")),
    path(API_V1 + "users/", include("apps.accounts.user_urls")),
    path(API_V1 + "sync/", include("apps.sync.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
