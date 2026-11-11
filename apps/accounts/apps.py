from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Contas e perfis"

    def ready(self):
        from . import signals  # noqa: F401
        from .perfis import sincronizar_perfis
        post_migrate.connect(sincronizar_perfis, dispatch_uid="siga_sincronizar_perfis")
