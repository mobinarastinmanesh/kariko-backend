from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.mixins import UserFilterMixin
from common.permissions import IsOwner

from .filters import TaskFilter
from .models import Step, Task
from .serializers import (
    StepSerializer,
    StepWriteSerializer,
    TaskSerializer,
    TaskWriteSerializer,
)


class TaskViewSet(UserFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Task.objects.all()
    filterset_class = TaskFilter
    search_fields = ["title", "notes"]
    ordering_fields = ["created_at", "updated_at", "due_date", "sort_order"]
    ordering = ["sort_order", "created_at"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_deleted=False)
            .select_related("task_list")
            .prefetch_related("steps")
            .annotate(
                steps_count=Count("steps", filter=Q(steps__is_deleted=False)),
                steps_done_count=Count(
                    "steps", filter=Q(steps__is_deleted=False, steps__done=True)
                ),
            )
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TaskWriteSerializer
        return TaskSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])


class StepViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StepSerializer

    def _get_task(self):
        return Task.objects.filter(
            pk=self.kwargs["task_pk"],
            user=self.request.user,
            is_deleted=False,
        ).first()

    def get_queryset(self):
        task = self._get_task()
        if not task:
            return Step.objects.none()
        return Step.objects.filter(task=task, is_deleted=False)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return StepWriteSerializer
        return StepSerializer

    def perform_create(self, serializer):
        task = self._get_task()
        if not task:
            from rest_framework.exceptions import NotFound
            raise NotFound("Task not found.")
        serializer.save(task=task)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])
