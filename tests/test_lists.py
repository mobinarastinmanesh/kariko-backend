import pytest

from apps.lists.models import TaskList
from apps.tasks.models import Task

LISTS_URL = "/api/v1/lists/"


def list_url(pk):
    return f"/api/v1/lists/{pk}/"


@pytest.mark.django_db
class TestListCRUD:
    def test_create_list(self, auth_client):
        res = auth_client.post(LISTS_URL, {"name": "Work", "color": "#f14254"})
        assert res.status_code == 201
        assert res.data["name"] == "Work"
        assert res.data["color"] == "#f14254"

    def test_list_scoped_to_user(self, auth_client, auth_client2, user, user2):
        TaskList.objects.create(user=user, name="My list", color="#f14254")
        TaskList.objects.create(user=user2, name="Their list", color="#3a84ca")
        res = auth_client.get(LISTS_URL)
        names = [l["name"] for l in res.data["results"]]
        assert "My list" in names
        assert "Their list" not in names

    def test_update_list(self, auth_client, user):
        lst = TaskList.objects.create(user=user, name="Old", color="#f14254")
        res = auth_client.patch(list_url(lst.pk), {"name": "New", "color": "#3a84ca"})
        assert res.status_code == 200
        assert res.data["name"] == "New"

    def test_delete_soft_deletes(self, auth_client, user):
        lst = TaskList.objects.create(user=user, name="Trash", color="#f14254")
        res = auth_client.delete(list_url(lst.pk))
        assert res.status_code == 204
        lst.refresh_from_db()
        assert lst.is_deleted is True

    def test_deleted_list_not_in_results(self, auth_client, user):
        lst = TaskList.objects.create(user=user, name="Gone", color="#f14254", is_deleted=True)
        res = auth_client.get(LISTS_URL)
        ids = [l["id"] for l in res.data["results"]]
        assert str(lst.pk) not in ids

    def test_task_count_annotation(self, auth_client, user):
        lst = TaskList.objects.create(user=user, name="Work", color="#f14254")
        Task.objects.create(user=user, task_list=lst, title="Active", done=False)
        Task.objects.create(user=user, task_list=lst, title="Done", done=True)
        res = auth_client.get(list_url(lst.pk))
        assert res.status_code == 200
        assert res.data["task_count"] == 1

    def test_cannot_access_other_users_list(self, auth_client2, user):
        lst = TaskList.objects.create(user=user, name="Private", color="#f14254")
        res = auth_client2.get(list_url(lst.pk))
        assert res.status_code in (403, 404)

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(LISTS_URL)
        assert res.status_code == 401
