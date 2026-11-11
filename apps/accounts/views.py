import qrcode
import qrcode.image.svg
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.audit.models import AuditEvent


class SigaLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class SigaLogoutView(LogoutView):
    pass


class CodigoForm(forms.Form):
    codigo = forms.CharField(
        label="Código de 6 dígitos", max_length=8, min_length=6,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code", "autofocus": True}))

    def clean_codigo(self):
        # Postel: aceita "123 456" ou "123-456".
        codigo = "".join(c for c in self.cleaned_data["codigo"] if c.isdigit())
        if len(codigo) != 6:
            raise forms.ValidationError("Digite os 6 números mostrados no aplicativo.")
        return codigo


def _proximo(request):
    destino = request.GET.get("next") or request.POST.get("next") or "/"
    if url_has_allowed_host_and_scheme(destino, {request.get_host()}, require_https=request.is_secure()):
        return destino
    return "/"


def _auditar(request, acao):
    AuditEvent.objects.create(actor=request.user, module="accounts", action=acao,
                              object_type="User", object_id=str(request.user.pk))


@login_required
@require_http_methods(["GET", "POST"])
def mfa_configurar(request):
    if TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
        return redirect("accounts:mfa_verificar")
    dispositivo, _ = TOTPDevice.objects.get_or_create(
        user=request.user, confirmed=False, defaults={"name": "Aplicativo autenticador"})
    form = CodigoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if dispositivo.verify_token(form.cleaned_data["codigo"]):
            with transaction.atomic():
                dispositivo.confirmed = True
                dispositivo.save(update_fields=["confirmed"])
                _auditar(request, "mfa_ativado")
            otp_login(request, dispositivo)
            return redirect(_proximo(request))
        form.add_error("codigo", "Código incorreto ou expirado. Confira a hora do celular e tente o próximo código.")
    qr = qrcode.make(dispositivo.config_url, image_factory=qrcode.image.svg.SvgPathImage, box_size=8)
    segredo = dispositivo.config_url.split("secret=")[1].split("&")[0]
    return render(request, "accounts/mfa_configurar.html", {
        "form": form, "qr_svg": mark_safe(qr.to_string(encoding="unicode")),
        "segredo": " ".join(segredo[i:i + 4] for i in range(0, len(segredo), 4)), "next": _proximo(request)})


@login_required
@require_http_methods(["GET", "POST"])
def mfa_verificar(request):
    dispositivos = TOTPDevice.objects.filter(user=request.user, confirmed=True)
    if not dispositivos.exists():
        return redirect("accounts:mfa_configurar")
    form = CodigoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        for dispositivo in dispositivos:
            if dispositivo.verify_is_allowed()[0] and dispositivo.verify_token(form.cleaned_data["codigo"]):
                otp_login(request, dispositivo)
                return redirect(_proximo(request))
        form.add_error("codigo", "Código incorreto ou expirado. Após várias tentativas, aguarde alguns segundos.")
    return render(request, "accounts/mfa_verificar.html", {"form": form, "next": _proximo(request)})
