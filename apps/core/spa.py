"""Entrega o app React (frontend/dist/index.html) só para usuários logados."""
import secrets

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from .middleware import SecurityHeadersMiddleware


@never_cache
@login_required
def app(request, caminho=""):
    indice = settings.SPA_DIR / "index.html"
    if not indice.exists():
        return render(request, "core/app_nao_compilado.html", status=503)
    # Nonce por requisição: os componentes de diálogo (Radix) criam um <style> para travar a rolagem
    # da página. Com o nonce a CSP continua sem 'unsafe-inline'.
    nonce = secrets.token_urlsafe(18)
    html = indice.read_text(encoding="utf-8").replace('content="__CSP_NONCE__"', f'content="{nonce}"')
    resposta = HttpResponse(html)
    resposta.headers["Content-Security-Policy"] = SecurityHeadersMiddleware.CSP.replace(
        "style-src 'self'", f"style-src 'self' 'nonce-{nonce}'")
    return resposta
