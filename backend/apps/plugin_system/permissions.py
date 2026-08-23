"""
Permissions for Tafakor Plugin System.
Validates topic ownership and administrative privileges for topic plugin installations.
"""
from rest_framework import permissions
from apps.notes.models import Topic


def is_topic_admin_or_owner(user, topic: Topic) -> bool:
    """
    Helper function checking if a user has administrative control over a topic.
    Returns True if:
    1. User is superuser.
    2. User is topic creator (created_by).
    3. User is listed in TopicAdmin for this topic.
    """
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    if topic.created_by_id and topic.created_by_id == user.id:
        return True
    if hasattr(topic, 'admins') and topic.admins.filter(user=user).exists():
        return True
    return False


class IsTopicAdminOrOwner(permissions.BasePermission):
    """
    Permission class guarding Topic Plugin endpoints:
    - SAFE methods (GET, HEAD, OPTIONS) are allowed for all users.
    - Mutations (POST, PUT, PATCH, DELETE) require the user to be:
      1. Superuser, OR
      2. Topic Creator (`topic.created_by == request.user`), OR
      3. Topic Admin (`topic.admins.filter(user=request.user).exists()`).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, 'is_superuser', False):
            return True

        # Resolve Topic instance from various object types
        topic = None
        if isinstance(obj, Topic):
            topic = obj
        elif hasattr(obj, 'topic'):
            topic = obj.topic

        if not topic:
            return False

        return is_topic_admin_or_owner(request.user, topic)
