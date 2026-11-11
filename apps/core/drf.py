"""Integração com o Django REST Framework (sem importar views, para evitar import circular)."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from rest_framework import permissions, status
from rest_framework.response import Response

from apps.accounts.mfa import exige_mfa


class UsuarioVerificado(permissions.BasePermission):
    """Logado e, quando o perfil exige, com MFA verificado nesta sessão."""
    message = "Confirme o código do aplicativo autenticador para continuar."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return not exige_mfa(user) or user.is_verified()


def tratar_excecao(exc, context):
    from apps.reformas.servicos import ConflitoDeVersao, RegraDeNegocio, SemPermissao
    if isinstance(exc, ConflitoDeVersao):
        return Response({"detail": str(exc), "codigo": "conflito"}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, SemPermissao):
        return Response({"detail": str(exc), "codigo": "sem_permissao"}, status=status.HTTP_403_FORBIDDEN)
    if isinstance(exc, RegraDeNegocio):
        return Response({"detail": str(exc), "codigo": "regra"}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, DjangoValidationError):
        campos = getattr(exc, "message_dict", None) or {"detail": exc.messages}
        return Response(campos, status=status.HTTP_400_BAD_REQUEST)
    from rest_framework.views import exception_handler
    resposta = exception_handler(exc, context)
    if resposta is not None and resposta.status_code in (401, 403) and not context["request"].user.is_authenticated:
        resposta.data = {"detail": "Sua sessão terminou. Entre novamente.", "codigo": "nao_autenticado",
                         "login": reverse("accounts:login")}
    return resposta


