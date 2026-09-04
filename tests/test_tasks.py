import uuid

import pytest

from apps.tasks.models import Step, Task

TASKS_URL = "/api/v1/tasks/"
LISTS_URL = "/api/v1/lists/"


def task_url(pk):
    return f"/api/v1/tasks/{pk}/"


def steps_url(task_pk):
    return f"/api/v1/tasks/{task_pk}/steps/"


def step_url(task_pk, step_pk):
    return f"/api/v1/tasks/{task_pk}/steps/{step_pk}/"


@pytest.mark.django_db
class TestTaskCRUD:
    def test_create_task(self, auth_client):
        res = auth_client.post(TASKS_URL, {"title": "Buy milk"})
        assert res.status_code == 201
        assert res.data["title"] == "Buy milk"
        assert res.data["done"] is False

    def test_list_tasks_scoped_to_user(self, auth_client, auth_client2, user, user2):
        Task.objects.create(user=user, title="User 1 task")
        Task.objects.create(user=user2, title="User 2 task")
        res = auth_client.get(TASKS_URL)
        titles = [t["title"] for t in res.data["results"]]
        assert "User 1 task" in titles
        assert "User 2 task" not in titles

    def test_update_task_title(self, auth_client, user):
        task = Task.objects.create(user=user, title="Old title")
        res = auth_client.patch(task_url(task.pk), {"title": "New title"})
        assert res.status_code == 200
        assert res.data["title"] == "New title"

    def test_toggle_done(self, auth_client, user):
        task = Task.objects.create(user=user, title="Test")
        res = auth_client.patch(task_url(task.pk), {"done": True})
        assert res.status_code == 200
        assert res.data["done"] is True

    def test_delete_soft_deletes(self, auth_client, user):
        task = Task.objects.create(user=user, title="Delete me")
        res = auth_client.delete(task_url(task.pk))
        assert res.status_code == 204
        task.refresh_from_db()
        assert task.is_deleted is True

    def test_deleted_task_not_in_list(self, auth_client, user):
        task = Task.objects.create(user=user, title="Gone", is_deleted=True)
        res = auth_client.get(TASKS_URL)
        ids = [t["id"] for t in res.data["results"]]
        assert str(task.pk) not in ids

    def test_cannot_access_other_users_task(self, auth_client2, user):
        task = Task.objects.create(user=user, title="Private")
        res = auth_client2.get(task_url(task.pk))
        assert res.status_code in (403, 404)

    def test_filter_my_day(self, auth_client, user):
        Task.objects.create(user=user, title="Normal task")
        Task.objects.create(user=user, title="My Day task", my_day=True)
        res = auth_client.get(TASKS_URL, {"my_day": True})
        titles = [t["title"] for t in res.data["results"]]
        assert "My Day task" in titles
        assert "Normal task" not in titles

    def test_filter_important(self, auth_client, user):
        Task.objects.create(user=user, title="Not important")
        Task.objects.create(user=user, title="Important!", important=True)
        res = auth_client.get(TASKS_URL, {"important": True})
        titles = [t["title"] for t in res.data["results"]]
        assert "Important!" in titles
        assert "Not important" not in titles

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(TASKS_URL)
        assert res.status_code == 401


@pytest.mark.django_db
class TestStepCRUD:
    def test_create_step(self, auth_client, user):
        task = Task.objects.create(user=user, title="Parent task")
        res = auth_client.post(steps_url(task.pk), {"title": "Step 1"})
        assert res.status_code == 201
        assert res.data["title"] == "Step 1"

    def test_list_steps(self, auth_client, user):
        task = Task.objects.create(user=user, title="Task")
        Step.objects.create(task=task, title="Step A")
        Step.objects.create(task=task, title="Step B")
        res = auth_client.get(steps_url(task.pk))
        assert res.status_code == 200
        assert len(res.data["results"]) == 2

    def test_toggle_step_done(self, auth_client, user):
        task = Task.objects.create(user=user, title="Task")
        step = Step.objects.create(task=task, title="Do it")
        res = auth_client.patch(step_url(task.pk, step.pk), {"done": True})
        assert res.status_code == 200
        assert res.data["done"] is True

    def test_delete_step_soft_deletes(self, auth_client, user):
        task = Task.objects.create(user=user, title="Task")
        step = Step.objects.create(task=task, title="Bye")
        res = auth_client.delete(step_url(task.pk, step.pk))
        assert res.status_code == 204
        step.refresh_from_db()
        assert step.is_deleted is True

    def test_cannot_add_step_to_other_users_task(self, auth_client2, user):
        task = Task.objects.create(user=user, title="Private task")
        res = auth_client2.post(steps_url(task.pk), {"title": "Intruder step"})
        assert res.status_code in (403, 404)
