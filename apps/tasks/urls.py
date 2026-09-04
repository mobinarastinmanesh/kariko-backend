from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import StepViewSet, TaskViewSet

router = DefaultRouter()
router.register("", TaskViewSet, basename="task")

steps_router = NestedDefaultRouter(router, "", lookup="task")
steps_router.register("steps", StepViewSet, basename="task-steps")

urlpatterns = router.urls + steps_router.urls
