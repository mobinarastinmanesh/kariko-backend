import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

OTP_REQUEST_URL = "/api/v1/auth/otp/request/"
OTP_VERIFY_URL = "/api/v1/auth/otp/verify/"
PASSWORD_LOGIN_URL = "/api/v1/auth/password/login/"
TOKEN_REFRESH_URL = "/api/v1/auth/token/refresh/"
LOGOUT_URL = "/api/v1/auth/logout/"
ME_URL = "/api/v1/users/me/"


@pytest.mark.django_db
class TestOTPRequest:
    def test_valid_phone_returns_200(self, api_client):
        res = api_client.post(OTP_REQUEST_URL, {"phone": "+989121234567"})
        assert res.status_code == 200

    def test_invalid_phone_returns_400(self, api_client):
        res = api_client.post(OTP_REQUEST_URL, {"phone": "notaphone"})
        assert res.status_code == 400

    def test_otp_stored_in_cache(self, api_client):
        cache.clear()
        api_client.post(OTP_REQUEST_URL, {"phone": "+989121234567"})
        stored = cache.get("otp:+989121234567")
        assert stored is not None
        assert len(stored) == 6


@pytest.mark.django_db
class TestOTPVerify:
    def test_correct_code_returns_tokens(self, api_client):
        cache.set("otp:+989121234567", "123456", timeout=120)
        res = api_client.post(OTP_VERIFY_URL, {"phone": "+989121234567", "code": "123456"})
        assert res.status_code == 200
        assert "access" in res.data
        assert "refresh" in res.data
        assert "user" in res.data

    def test_first_login_creates_user(self, api_client, db):
        cache.set("otp:+989120000001", "999999", timeout=120)
        assert not User.objects.filter(phone="+989120000001").exists()
        api_client.post(OTP_VERIFY_URL, {"phone": "+989120000001", "code": "999999"})
        assert User.objects.filter(phone="+989120000001").exists()

    def test_wrong_code_returns_400(self, api_client):
        cache.set("otp:+989121234567", "123456", timeout=120)
        res = api_client.post(OTP_VERIFY_URL, {"phone": "+989121234567", "code": "000000"})
        assert res.status_code == 400

    def test_expired_code_returns_400(self, api_client):
        # Nothing in cache → treat as expired
        cache.delete("otp:+989121234567")
        res = api_client.post(OTP_VERIFY_URL, {"phone": "+989121234567", "code": "123456"})
        assert res.status_code == 400

    def test_code_deleted_after_use(self, api_client):
        cache.set("otp:+989121234568", "111111", timeout=120)
        api_client.post(OTP_VERIFY_URL, {"phone": "+989121234568", "code": "111111"})
        assert cache.get("otp:+989121234568") is None


@pytest.mark.django_db
class TestPasswordLogin:
    def test_correct_credentials_return_tokens(self, api_client, user):
        user.set_password("secret123")
        user.save()
        res = api_client.post(PASSWORD_LOGIN_URL, {"phone": user.phone, "password": "secret123"})
        assert res.status_code == 200
        assert "access" in res.data
        assert "refresh" in res.data
        assert "user" in res.data
        assert res.data["user"]["phone"] == user.phone

    def test_wrong_password_returns_400(self, api_client, user):
        user.set_password("correct")
        user.save()
        res = api_client.post(PASSWORD_LOGIN_URL, {"phone": user.phone, "password": "wrong"})
        assert res.status_code == 400

    def test_nonexistent_phone_returns_400(self, api_client):
        res = api_client.post(PASSWORD_LOGIN_URL, {"phone": "+989000000099", "password": "x"})
        assert res.status_code == 400

    def test_missing_fields_returns_400(self, api_client):
        assert api_client.post(PASSWORD_LOGIN_URL, {"phone": "+989121234567"}).status_code == 400
        assert api_client.post(PASSWORD_LOGIN_URL, {"password": "pw"}).status_code == 400
        assert api_client.post(PASSWORD_LOGIN_URL, {}).status_code == 400

    def test_user_without_password_returns_400(self, api_client, user):
        # user fixture has no password set (unusable password)
        res = api_client.post(PASSWORD_LOGIN_URL, {"phone": user.phone, "password": "anything"})
        assert res.status_code == 400

    def test_returned_token_is_usable(self, api_client, user):
        user.set_password("pass1234")
        user.save()
        login_res = api_client.post(PASSWORD_LOGIN_URL, {"phone": user.phone, "password": "pass1234"})
        assert login_res.status_code == 200
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_res.data['access']}")
        me_res = api_client.get(ME_URL)
        assert me_res.status_code == 200
        assert me_res.data["phone"] == user.phone


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_returns_new_access_token(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        res = api_client.post(TOKEN_REFRESH_URL, {"refresh": str(refresh)})
        assert res.status_code == 200
        assert "access" in res.data

    def test_invalid_refresh_returns_401(self, api_client):
        res = api_client.post(TOKEN_REFRESH_URL, {"refresh": "not.a.token"})
        assert res.status_code == 401


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, auth_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        res = auth_client.delete(LOGOUT_URL, {"refresh": str(refresh)}, format="json")
        assert res.status_code == 204
        # Attempt to use the same refresh token → should fail
        refresh_res = auth_client.post(TOKEN_REFRESH_URL, {"refresh": str(refresh)})
        assert refresh_res.status_code == 401

    def test_logout_requires_auth(self, api_client):
        res = api_client.delete(LOGOUT_URL, {"refresh": "x"}, format="json")
        assert res.status_code == 401


@pytest.mark.django_db
class TestMeView:
    def test_get_me(self, auth_client):
        res = auth_client.get(ME_URL)
        assert res.status_code == 200
        assert "first_name" in res.data

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(ME_URL)
        assert res.status_code == 401

    def test_update_first_name(self, auth_client):
        res = auth_client.patch(ME_URL, {"first_name": "Alice"})
        assert res.status_code == 200
        assert res.data["first_name"] == "Alice"

    def test_update_language(self, auth_client):
        res = auth_client.patch(ME_URL, {"language": "fa"})
        assert res.status_code == 200
        assert res.data["language"] == "fa"
