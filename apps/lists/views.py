from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.mixins import UserFilterMixin
from common.permissions import IsOwner

from .models import TaskList
from .serializers import TaskListSerializer, TaskListWriteSerializer


class TaskListViewSet(UserFilterMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = TaskList.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_deleted=False)
            .annotate(task_count=Count("tasks", filter=Q(tasks__done=False, tasks__is_deleted=False)))
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TaskListWriteSerializer
        return TaskListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])
