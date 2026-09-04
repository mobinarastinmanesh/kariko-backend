from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LogoutView, OTPRequestView, OTPVerifyView, PasswordLoginView

urlpatterns = [
    path("otp/request/", OTPRequestView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("password/login/", PasswordLoginView.as_view(), name="password-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
