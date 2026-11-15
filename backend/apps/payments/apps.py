from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Django AppConfig for the centralized Tafakor payment gateway module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    verbose_name = "درگاه و تراکنش‌های متمرکز پرداخت"

