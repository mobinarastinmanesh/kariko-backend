class UserFilterMixin:
    """Automatically scope all queryset reads to the authenticated user."""

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
