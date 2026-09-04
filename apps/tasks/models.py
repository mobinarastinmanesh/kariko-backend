import uuid

from django.conf import settings
from django.db import models


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks"
    )
    task_list = models.ForeignKey(
        "lists.TaskList",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    title = models.CharField(max_length=512)
    notes = models.TextField(blank=True)
    done = models.BooleanField(default=False)
    important = models.BooleanField(default=False)
    my_day = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    reminder_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    done_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "tasks_task"
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["user", "done", "is_deleted"]),
            models.Index(fields=["user", "my_day"]),
            models.Index(fields=["user", "important"]),
            models.Index(fields=["user", "due_date"]),
        ]

    def __str__(self):
        return self.title


class Step(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField(max_length=512)
    done = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "tasks_step"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return self.title
