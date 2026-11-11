"""Sincroniza os Grupos (perfis) e suas permissões após cada `migrate`. Idempotente."""
from django.contrib.auth.models import Group, Permission

from apps.core.access import ADMINISTRADOR, DIRETORIA, GESTOR, SOLICITANTE

APPS_SIGA = ["core", "accounts", "requests_center", "assets", "fleet", "travels", "contracts", "audit", "reformas"]
OPERACAO = ["requests_center", "assets", "fleet", "travels", "contracts", "reformas"]


def _perms(apps_label, acoes):
    return Permission.objects.filter(content_type__app_label__in=apps_label, codename__regex=rf"^({'|'.join(acoes)})_")


def sincronizar_perfis(**kwargs):
    regras = {
        ADMINISTRADOR: _perms(APPS_SIGA, ["view", "add", "change", "delete"]).exclude(
            content_type__app_label="audit", codename__regex=r"^(add|change|delete)_")
        | Permission.objects.filter(content_type__app_label="auth", content_type__model="user"),
        GESTOR: _perms(OPERACAO, ["view", "add", "change"]) | _perms(["core"], ["view"]),
        DIRETORIA: _perms(APPS_SIGA, ["view"]),
        SOLICITANTE: Permission.objects.filter(codename__in=["add_administrativerequest", "add_travelrequest"]),
    }
    for nome, perms in regras.items():
        grupo, _ = Group.objects.get_or_create(name=nome)
        grupo.permissions.set(perms.distinct())
