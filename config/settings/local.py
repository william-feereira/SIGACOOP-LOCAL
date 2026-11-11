"""Configuração para rodar o SIGA na própria máquina (http://localhost), sem HTTPS.

Igual à produção no que importa (DEBUG desligado, PostgreSQL, CSP, MFA, bloqueio de login),
mas sem exigir HTTPS, porque não há certificado em localhost. Não use em servidor.
"""
from .base import *

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [x.strip() for x in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SIGA_PERMITIR_DEMO = True

if SECRET_KEY == "gere-uma-chave-segura" or len(SECRET_KEY) < 32:
    raise RuntimeError("Defina SECRET_KEY no .env (o script de início gera uma automaticamente).")
