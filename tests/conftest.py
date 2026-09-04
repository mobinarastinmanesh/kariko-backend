import os

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


def pytest_configure(config):
    # Force test settings even when container env has DJANGO_SETTINGS_MODULE set
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="+989121234567")


@pytest.fixture
def user2(db):
    return User.objects.create_user(phone="+989129876543")


@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def auth_client2(api_client, user2):
    client = APIClient()
    refresh = RefreshToken.for_user(user2)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client
