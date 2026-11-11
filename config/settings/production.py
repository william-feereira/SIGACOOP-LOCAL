from .base import *
DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
# Domínio interno: HSTS em subdomínios e preload são decisões de infraestrutura, não do app.
SILENCED_SYSTEM_CHECKS=["security.W005","security.W021"]
if os.environ.get("TRUST_PROXY", "False").lower() == "true":
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")
    # Nginx envia o IP real em X-Real-IP; sem isso o bloqueio de login veria só 127.0.0.1.
    AXES_IPWARE_PROXY_COUNT=1
    AXES_IPWARE_META_PRECEDENCE_ORDER=["HTTP_X_REAL_IP","REMOTE_ADDR"]
if len(SECRET_KEY)<50 or SECRET_KEY=="gere-uma-chave-segura":
    raise RuntimeError("SECRET_KEY de produção deve ser aleatória e conter pelo menos 50 caracteres.")
if DB_ENGINE != "postgresql":
    raise RuntimeError("Produção exige PostgreSQL.")
SECURE_REFERRER_POLICY="same-origin"
if ENTRA_ENABLED:
    raise RuntimeError("Entra ID ainda não foi implementado. Não habilite a opção como substituto de MFA.")
