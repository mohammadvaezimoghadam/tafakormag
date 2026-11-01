from django.apps import AppConfig


class QuranConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.quran'
    verbose_name = 'Official Quran Plugin'

    def ready(self):
        pass
