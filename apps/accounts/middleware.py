from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from .mfa import exige_mfa

LIVRES = ("/contas/", "/static/", "/privacidade/", "/termos/")


class MfaObrigatorioMiddleware:
    """Usuário que precisa de MFA só navega depois de verificar o código do aplicativo."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (user is not None and exige_mfa(user) and not user.is_verified()
                and not request.path.startswith(LIVRES)):
            from django_otp.plugins.otp_totp.models import TOTPDevice
            tem_dispositivo = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
            destino = "accounts:mfa_verificar" if tem_dispositivo else "accounts:mfa_configurar"
            if request.path.startswith("/api/"):
                return JsonResponse({"detail": "Confirme o código do aplicativo autenticador.", "codigo": "mfa",
                                     "login": reverse(destino)}, status=403)
            return redirect(f"{reverse(destino)}?next={request.get_full_path()}")
        return self.get_response(request)
