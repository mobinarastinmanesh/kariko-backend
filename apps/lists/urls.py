from rest_framework.routers import DefaultRouter

from .views import TaskListViewSet

router = DefaultRouter()
router.register("", TaskListViewSet, basename="list")

urlpatterns = router.urls
