from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class OTPRequestSerializer(serializers.Serializer):
    phone = PhoneNumberField()


class OTPVerifySerializer(serializers.Serializer):
    phone = PhoneNumberField()
    code = serializers.CharField(min_length=4, max_length=8)


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return UserSerializer(obj["user"]).data


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "language", "theme", "avatar", "created_at"]
        read_only_fields = ["id", "phone", "created_at"]

    def get_phone(self, obj):
        return str(obj.phone)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "language", "theme", "avatar"]


class PasswordLoginSerializer(serializers.Serializer):
    phone = PhoneNumberField()
    password = serializers.CharField(min_length=4, write_only=True)
