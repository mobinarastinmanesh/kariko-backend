from django.urls import path

from .views import SyncView

urlpatterns = [
    path("", SyncView.as_view(), name="sync"),
]
