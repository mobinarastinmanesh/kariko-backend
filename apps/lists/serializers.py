from rest_framework import serializers

from .models import TaskList


class TaskListSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TaskList
        fields = [
            "id", "name", "color", "icon", "sort_order",
            "task_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "task_count"]


class TaskListWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskList
        fields = ["name", "color", "icon", "sort_order"]
