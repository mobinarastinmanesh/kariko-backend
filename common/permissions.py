from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Allow access only to the object owner. Object must have a `user` FK."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
