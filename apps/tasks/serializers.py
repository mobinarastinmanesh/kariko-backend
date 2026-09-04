from rest_framework import serializers

from .models import Step, Task


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ["id", "title", "done", "sort_order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ["title", "done", "sort_order"]


class TaskSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)
    steps_count = serializers.IntegerField(read_only=True)
    steps_done_count = serializers.IntegerField(read_only=True)
    list_id = serializers.UUIDField(source="task_list_id", allow_null=True, required=False)
    list_name = serializers.CharField(source="task_list.name", read_only=True, allow_null=True)
    list_color = serializers.CharField(source="task_list.color", read_only=True, allow_null=True)

    class Meta:
        model = Task
        fields = [
            "id", "title", "notes", "done", "important", "my_day",
            "due_date", "reminder_at", "sort_order",
            "list_id", "list_name", "list_color",
            "steps", "steps_count", "steps_done_count",
            "done_at", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "done_at"]


class TaskWriteSerializer(serializers.ModelSerializer):
    list_id = serializers.UUIDField(source="task_list_id", allow_null=True, required=False)

    class Meta:
        model = Task
        fields = [
            "title", "notes", "done", "important", "my_day",
            "due_date", "reminder_at", "sort_order", "list_id",
        ]

    def validate_list_id(self, value):
        if value is None:
            return value
        user = self.context["request"].user
        from apps.lists.models import TaskList
        if not TaskList.objects.filter(id=value, user=user, is_deleted=False).exists():
            raise serializers.ValidationError("List not found.")
        return value

    def update(self, instance, validated_data):
        # Auto-stamp done_at
        if "done" in validated_data:
            from django.utils import timezone
            if validated_data["done"] and not instance.done:
                validated_data["done_at"] = timezone.now()
            elif not validated_data["done"]:
                validated_data["done_at"] = None
        return super().update(instance, validated_data)
