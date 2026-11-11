from django.conf import settings

from apps.core.access import tem_perfil


def exige_mfa(user) -> bool:
    """MFA obrigatório para perfis sensíveis e para quem acessa o /admin/."""
    if not getattr(user, "is_authenticated", False):
        return False
    return user.is_staff or user.is_superuser or tem_perfil(user, *settings.SIGA_MFA_PERFIS)
