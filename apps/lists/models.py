import uuid

from django.conf import settings
from django.db import models


class TaskList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_lists"
    )
    name = models.CharField(max_length=128)
    color = models.CharField(max_length=7, default="#8b8580")  # hex
    icon = models.CharField(max_length=8, blank=True)           # emoji
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "lists_tasklist"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return self.name
