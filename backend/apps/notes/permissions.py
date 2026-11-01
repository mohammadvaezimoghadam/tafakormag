from rest_framework import permissions
from .models import Topic


class IsTopicOwnerOrAdmin(permissions.BasePermission):
    """
    Custom Permission Guard:
    - SAFE methods (GET, HEAD, OPTIONS) are open to all users (Public Access).
    - Mutation methods (POST, PUT, PATCH, DELETE) require the user to be either:
      1. The Topic Creator (Owner), OR
      2. An explicitly assigned record in TopicAdmin for the target topic, OR
      3. A superuser.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user and request.user.is_superuser:
            return True

        # Extract topic instance whether `obj` is a Topic or a Post associated with a Topic
        topic = obj if isinstance(obj, Topic) else getattr(obj, 'topic', None)
        if not topic:
            return False

        # Check ownership
        is_owner = (topic.created_by == request.user) if topic.created_by else False

        # Check admin role
        is_admin = topic.admins.filter(user=request.user).exists()

        return is_owner or is_admin
