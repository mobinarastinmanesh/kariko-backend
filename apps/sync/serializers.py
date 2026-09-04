from rest_framework import serializers


class SyncPushSerializer(serializers.Serializer):
    changes = serializers.DictField()
    last_pulled_at = serializers.IntegerField(allow_null=True, required=False)
