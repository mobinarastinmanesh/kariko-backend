import time

import pytest

from apps.lists.models import TaskList
from apps.tasks.models import Step, Task

SYNC_URL = "/api/v1/sync/"


def _make_id():
    import uuid
    return str(uuid.uuid4())


@pytest.mark.django_db
class TestSyncPull:
    def test_pull_returns_structure(self, auth_client):
        res = auth_client.get(SYNC_URL)
        assert res.status_code == 200
        assert "changes" in res.data
        assert "timestamp" in res.data
        assert set(res.data["changes"].keys()) == {"tasks", "steps", "lists"}

    def test_initial_pull_returns_all_records(self, auth_client, user):
        TaskList.objects.create(user=user, name="L1", color="#f14254")
        Task.objects.create(user=user, title="T1")
        res = auth_client.get(SYNC_URL)
        assert len(res.data["changes"]["lists"]["created"]) == 1
        assert len(res.data["changes"]["tasks"]["created"]) == 1

    def test_pull_scoped_to_user(self, auth_client, user2):
        Task.objects.create(user=user2, title="Other user's task")
        res = auth_client.get(SYNC_URL)
        assert len(res.data["changes"]["tasks"]["created"]) == 0

    def test_incremental_pull_returns_only_new(self, auth_client, user):
        Task.objects.create(user=user, title="Old task")
        time.sleep(0.05)  # ensure old task timestamp is safely behind ts
        ts = int(time.time() * 1000)
        time.sleep(0.05)
        Task.objects.create(user=user, title="New task")
        res = auth_client.get(SYNC_URL, {"last_pulled_at": ts})
        titles = [t["title"] for t in res.data["changes"]["tasks"]["created"]]
        assert "New task" in titles
        assert "Old task" not in titles

    def test_deleted_records_appear_in_deleted_list(self, auth_client, user):
        task = Task.objects.create(user=user, title="Delete me")
        ts = int(time.time() * 1000)
        time.sleep(0.05)
        task.is_deleted = True
        task.save()
        res = auth_client.get(SYNC_URL, {"last_pulled_at": ts})
        assert str(task.pk) in res.data["changes"]["tasks"]["deleted"]

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(SYNC_URL)
        assert res.status_code == 401


@pytest.mark.django_db
class TestSyncPush:
    def test_push_creates_task(self, auth_client):
        task_id = _make_id()
        payload = {
            "changes": {
                "tasks": {"created": [{"id": task_id, "title": "Pushed task", "done": False, "important": False, "my_day": False, "sort_order": 0}], "updated": [], "deleted": []},
                "steps": {"created": [], "updated": [], "deleted": []},
                "lists": {"created": [], "updated": [], "deleted": []},
            },
            "last_pulled_at": None,
        }
        res = auth_client.post(SYNC_URL, payload, format="json")
        assert res.status_code == 200
        assert Task.objects.filter(id=task_id).exists()

    def test_push_updates_task(self, auth_client, user):
        task = Task.objects.create(user=user, title="Original")
        payload = {
            "changes": {
                "tasks": {"created": [], "updated": [{"id": str(task.pk), "title": "Updated", "done": False, "important": False, "my_day": False, "sort_order": 0}], "deleted": []},
                "steps": {"created": [], "updated": [], "deleted": []},
                "lists": {"created": [], "updated": [], "deleted": []},
            },
            "last_pulled_at": None,
        }
        auth_client.post(SYNC_URL, payload, format="json")
        task.refresh_from_db()
        assert task.title == "Updated"

    def test_push_deletes_task(self, auth_client, user):
        task = Task.objects.create(user=user, title="Delete via sync")
        payload = {
            "changes": {
                "tasks": {"created": [], "updated": [], "deleted": [str(task.pk)]},
                "steps": {"created": [], "updated": [], "deleted": []},
                "lists": {"created": [], "updated": [], "deleted": []},
            },
            "last_pulled_at": None,
        }
        auth_client.post(SYNC_URL, payload, format="json")
        task.refresh_from_db()
        assert task.is_deleted is True

    def test_push_creates_step(self, auth_client, user):
        task = Task.objects.create(user=user, title="Task with step")
        step_id = _make_id()
        payload = {
            "changes": {
                "tasks": {"created": [], "updated": [], "deleted": []},
                "steps": {"created": [{"id": step_id, "task_id": str(task.pk), "title": "Step 1", "done": False, "sort_order": 0}], "updated": [], "deleted": []},
                "lists": {"created": [], "updated": [], "deleted": []},
            },
            "last_pulled_at": None,
        }
        res = auth_client.post(SYNC_URL, payload, format="json")
        assert res.status_code == 200
        assert Step.objects.filter(id=step_id).exists()

    def test_push_cannot_create_task_for_other_user(self, auth_client2, user):
        task_id = _make_id()
        payload = {
            "changes": {
                "tasks": {"created": [{"id": task_id, "title": "Hijack", "done": False, "important": False, "my_day": False, "sort_order": 0}], "updated": [], "deleted": []},
                "steps": {"created": [], "updated": [], "deleted": []},
                "lists": {"created": [], "updated": [], "deleted": []},
            },
            "last_pulled_at": None,
        }
        auth_client2.post(SYNC_URL, payload, format="json")
        task = Task.objects.filter(id=task_id).first()
        # Task is created but owned by user2, not user
        assert task is not None
        assert task.user != user

    def test_push_idempotent_create(self, auth_client, user):
        task_id = _make_id()
        payload = {
            "changes": {
                "tasks": {"created": [{"id": task_id, "title": "Idempotent", "done": False, "important": False, "my_day": False, "sort_order": 0}], "updated": [], "deleted": []},
                "steps": {"created": [], "updated": [], "deleted": []},
                "lists": {"created": [], "updated": [], "deleted": []},
            },
            "last_pulled_at": None,
        }
        auth_client.post(SYNC_URL, payload, format="json")
        auth_client.post(SYNC_URL, payload, format="json")
        assert Task.objects.filter(id=task_id).count() == 1
