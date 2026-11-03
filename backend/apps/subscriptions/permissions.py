from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from .utils import has_active_subscription


class HasPluginSubscription(permissions.BasePermission):
    """
    کلاس پرمیژن استاندارد DRF جهت بررسی اشتراک فعال کاربر برای یک پلاگین معین.
    در صورت عدم دسترسی، پیام خطای اختصاصی همراه با کد خطا بازمی‌گرداند.
    """
    plugin_identifier = None
    message = "برای استفاده از این بخش، نیاز به تهیه یا تمدید اشتراک ویژه دارید."

    def __init__(self, plugin_identifier: str = None):
        if plugin_identifier:
            self.plugin_identifier = plugin_identifier

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        target_plugin = self.plugin_identifier or getattr(view, 'plugin_identifier', None)
        if not target_plugin:
            return True

        has_access = has_active_subscription(request.user, target_plugin)
        if not has_access:
            raise PermissionDenied({
                'code': 'SUBSCRIPTION_REQUIRED',
                'plugin': target_plugin,
                'detail': self.message
            })

        return True


def has_subscription(plugin_identifier: str):
    """
    فکتوری جهت استفاده راحت در پرمیژن‌های ویو یا اکشن:
    permission_classes = [has_subscription('quran')]
    """
    class DynamicPluginPermission(HasPluginSubscription):
        plugin_identifier = plugin_identifier

    return DynamicPluginPermission

