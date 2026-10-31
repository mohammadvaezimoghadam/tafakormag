from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Lightweight, non-intrusive base ModelSerializer for the Marketplace plugin.
    Features:
    - Automatically marks system audit fields (id, created_at, updated_at, deleted_at) as read-only.
    - Provides safe access to the authenticated user via `self.current_user`.
    - Supports dynamic sparse fieldsets (e.g., MySerializer(item, fields=['id', 'title'])).
    - Preserves 100% standard DRF behavior and Meta definitions without rigid constraints.
    """
    DEFAULT_READ_ONLY_FIELDS = ("id", "created_at", "updated_at", "deleted_at")

    def __init__(self, *args, **kwargs):
        # Allow dynamic sparse field selection via kwargs
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name, None)

    def get_fields(self):
        """
        Dynamically ensures audit fields are read-only without overriding child Meta.read_only_fields.
        """
        fields = super().get_fields()
        for field_name in self.DEFAULT_READ_ONLY_FIELDS:
            if field_name in fields:
                fields[field_name].read_only = True
        return fields

    @property
    def current_user(self):
        """
        Safely retrieves the authenticated user from the serializer context.
        Returns None if request is unauthenticated or unavailable.
        """
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

    @property
    def request(self):
        """
        Convenience accessor for the current HTTP request.
        """
        return self.context.get("request")


class BaseInputSerializer(serializers.Serializer):
    """
    Minimal base serializer for action payloads and non-model command inputs
    (e.g., checkout parameters, gateway verification inputs).
    """

    @property
    def current_user(self):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

    @property
    def request(self):
        return self.context.get("request")
