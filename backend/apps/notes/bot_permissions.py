from django.conf import settings
from rest_framework.permissions import BasePermission


class IsBotService(BasePermission):
    """
    اگر BOT_API_KEY در settings تنظیم شده باشد، هدر X-Bot-API-Key باید همان مقدار باشد.
    اگر کلید خالی باشد (توسعه محلی)، بررسی هدر انجام نمی‌شود.
    """

    def has_permission(self, request, view):
        expected = (getattr(settings, "BOT_API_KEY", None) or "").strip()
        if not expected:
            return True
        provided = (request.headers.get("X-Bot-API-Key") or "").strip()
        return provided == expected
