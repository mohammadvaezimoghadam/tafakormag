from django.dispatch import Signal

# سیگنال رویداد فعال‌سازی یا تمدید اشتراک
# ارسال‌کننده‌ها: سرویس وریفای کافه‌بازار یا درگاه پرداخت
# پارامترها: user_subscription, user, plugin_identifier, plan, is_renewal
subscription_activated = Signal()

# سیگنال انقضای اشتراک
subscription_expired = Signal()

