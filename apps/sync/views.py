import datetime

from django.db import transaction
from django.db.models import Count, Q
from datetime import timezone as _tz

from django.utils.timezone import make_aware, now

utc = _tz.utc
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lists.models import TaskList
from apps.tasks.models import Step, Task

from .serializers import SyncPushSerializer


def _ts_to_dt(ts):
    """Unix ms timestamp → aware datetime."""
    if not ts:
        return None
    naive = datetime.datetime.utcfromtimestamp(int(ts) / 1000)
    return make_aware(naive, utc)


def _dt_to_ts(dt):
    """Aware datetime → Unix ms timestamp."""
    if not dt:
        return None
    return int(dt.timestamp() * 1000)


def _serialize_task(task):
    return {
        "id": str(task.id),
        "title": task.title,
        "notes": task.notes,
        "done": task.done,
        "important": task.important,
        "my_day": task.my_day,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "list_id": str(task.task_list_id) if task.task_list_id else None,
        "sort_order": task.sort_order,
        # Annotated counts populated by the queryset
        "steps_count": getattr(task, "steps_count", 0),
        "steps_done_count": getattr(task, "steps_done_count", 0),
        "created_at": _dt_to_ts(task.created_at),
        "updated_at": _dt_to_ts(task.updated_at),
    }


def _serialize_step(step):
    return {
        "id": str(step.id),
        "task_id": str(step.task_id),
        "title": step.title,
        "done": step.done,
        "sort_order": step.sort_order,
        "created_at": _dt_to_ts(step.created_at),
        "updated_at": _dt_to_ts(step.updated_at),
    }


def _serialize_list(lst):
    return {
        "id": str(lst.id),
        "name": lst.name,
        "color": lst.color,
        "icon": lst.icon,
        "sort_order": lst.sort_order,
        "created_at": _dt_to_ts(lst.created_at),
        "updated_at": _dt_to_ts(lst.updated_at),
    }


def _annotated_tasks(base_qs):
    return base_qs.annotate(
        steps_count=Count("steps", filter=Q(steps__is_deleted=False)),
        steps_done_count=Count("steps", filter=Q(steps__is_deleted=False, steps__done=True)),
    )


class SyncView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Pull: return all changes since last_pulled_at."""
        last_pulled_at = request.query_params.get("last_pulled_at")
        since = _ts_to_dt(last_pulled_at)
        user = request.user
        server_now = int(now().timestamp() * 1000)

        def _changes(qs_live, qs_deleted, serializer_fn, annotate_fn=None):
            if annotate_fn:
                qs_live = annotate_fn(qs_live)
            if since:
                # All records changed since lastPulledAt go into "updated".
                # WatermelonDB upserts "updated" records (creates if missing locally),
                # so this avoids the "server wants to create a record that already
                # exists locally" error that occurs when a client pushes a record
                # after the pull timestamp was captured.
                created = []
                updated = list(qs_live.filter(updated_at__gt=since))
                deleted = [
                    str(pk)
                    for pk in qs_deleted.filter(updated_at__gt=since).values_list("id", flat=True)
                ]
            else:
                created = list(qs_live)
                updated = []
                deleted = []
            return {
                "created": [serializer_fn(o) for o in created],
                "updated": [serializer_fn(o) for o in updated],
                "deleted": deleted,
            }

        tasks_live = Task.objects.filter(user=user, is_deleted=False)
        tasks_deleted = Task.objects.filter(user=user, is_deleted=True)
        steps_live = Step.objects.filter(task__user=user, is_deleted=False)
        steps_deleted = Step.objects.filter(task__user=user, is_deleted=True)
        lists_live = TaskList.objects.filter(user=user, is_deleted=False)
        lists_deleted = TaskList.objects.filter(user=user, is_deleted=True)

        return Response(
            {
                "changes": {
                    "tasks": _changes(tasks_live, tasks_deleted, _serialize_task, _annotated_tasks),
                    "steps": _changes(steps_live, steps_deleted, _serialize_step),
                    "lists": _changes(lists_live, lists_deleted, _serialize_list),
                },
                "timestamp": server_now,
            }
        )

    @transaction.atomic
    def post(self, request):
        """Push: apply client changes to the server."""
        serializer = SyncPushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        changes = serializer.validated_data["changes"]
        user = request.user

        self._apply_lists(changes.get("lists", {}), user)
        self._apply_tasks(changes.get("tasks", {}), user)
        self._apply_steps(changes.get("steps", {}), user)

        return Response({"ok": True}, status=status.HTTP_200_OK)

    def _apply_lists(self, changes, user):
        for raw in changes.get("created", []) + changes.get("updated", []):
            # An id collision with a record owned by a different user must never
            # let this request take it over — ignore it instead of reassigning
            # ownership. This can legitimately happen when a device that was
            # previously logged into another account still has stale local
            # records queued for push.
            existing = TaskList.objects.filter(id=raw["id"]).first()
            if existing and existing.user_id != user.id:
                continue
            TaskList.objects.update_or_create(
                id=raw["id"],
                defaults={
                    "user": user,
                    "name": raw.get("name", ""),
                    "color": raw.get("color", "#8b8580"),
                    "icon": raw.get("icon", ""),
                    "sort_order": raw.get("sort_order", 0),
                },
            )
        TaskList.objects.filter(
            id__in=changes.get("deleted", []), user=user
        ).update(is_deleted=True)

    def _apply_tasks(self, changes, user):
        for raw in changes.get("created", []) + changes.get("updated", []):
            existing = Task.objects.filter(id=raw["id"]).first()
            if existing and existing.user_id != user.id:
                continue
            # A referenced list must also belong to this user, otherwise drop
            # the reference rather than linking a task into someone else's list.
            list_id = raw.get("list_id") or None
            if list_id and not TaskList.objects.filter(id=list_id, user=user).exists():
                list_id = None
            Task.objects.update_or_create(
                id=raw["id"],
                defaults={
                    "user": user,
                    "title": raw.get("title", ""),
                    "notes": raw.get("notes", ""),
                    "done": raw.get("done", False),
                    "important": raw.get("important", False),
                    "my_day": raw.get("my_day", False),
                    "due_date": raw.get("due_date") or None,
                    "task_list_id": list_id,
                    "sort_order": raw.get("sort_order", 0),
                },
            )
        Task.objects.filter(
            id__in=changes.get("deleted", []), user=user
        ).update(is_deleted=True)

    def _apply_steps(self, changes, user):
        for raw in changes.get("created", []) + changes.get("updated", []):
            task = Task.objects.filter(id=raw.get("task_id"), user=user).first()
            if not task:
                continue
            existing = Step.objects.select_related("task").filter(id=raw["id"]).first()
            if existing and existing.task.user_id != user.id:
                continue
            Step.objects.update_or_create(
                id=raw["id"],
                defaults={
                    "task": task,
                    "title": raw.get("title", ""),
                    "done": raw.get("done", False),
                    "sort_order": raw.get("sort_order", 0),
                },
            )
        Step.objects.filter(
            id__in=changes.get("deleted", []), task__user=user
        ).update(is_deleted=True)
