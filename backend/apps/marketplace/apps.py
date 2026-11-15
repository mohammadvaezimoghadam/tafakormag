from django.apps import AppConfig


class MarketplaceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.marketplace"
    verbose_name = "Marketplace"

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save

        from .handlers import (
            link_pending_gifts_on_user_save,
            register_marketplace_payment_handlers,
        )

        register_marketplace_payment_handlers()
        User = get_user_model()
        post_save.connect(link_pending_gifts_on_user_save, sender=User)
