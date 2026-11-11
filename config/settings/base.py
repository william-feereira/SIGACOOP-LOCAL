from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY obrigatoria. Copie .env.example para .env.")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [x.strip() for x in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]
INSTALLED_APPS = [
 "django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles",
 "django_otp","django_otp.plugins.otp_totp","axes","rest_framework",
 "apps.core","apps.accounts","apps.audit","apps.requests_center","apps.assets","apps.fleet","apps.travels","apps.contracts","apps.analytics","apps.reformas",
]
MIDDLEWARE = [
 "django.middleware.security.SecurityMiddleware","whitenoise.middleware.WhiteNoiseMiddleware","django.contrib.sessions.middleware.SessionMiddleware",
 "django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware",
 "django_otp.middleware.OTPMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware",
 "apps.core.middleware.SecurityHeadersMiddleware","apps.accounts.middleware.MfaObrigatorioMiddleware","axes.middleware.AxesMiddleware",
]
AUTHENTICATION_BACKENDS=["axes.backends.AxesStandaloneBackend","django.contrib.auth.backends.ModelBackend"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages","apps.core.context_processors.navegacao"]}}]
WSGI_APPLICATION="config.wsgi.application"
ASGI_APPLICATION="config.asgi.application"
DB_ENGINE=os.environ.get("DB_ENGINE","postgresql")
if DB_ENGINE == "sqlite":
 DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
else:
 DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.environ.get("POSTGRES_DB","siga_coop"),"USER":os.environ.get("POSTGRES_USER","siga_app"),"PASSWORD":os.environ.get("POSTGRES_PASSWORD",""),"HOST":os.environ.get("POSTGRES_HOST","db"),"PORT":os.environ.get("POSTGRES_PORT","5432"),"CONN_MAX_AGE":60,"OPTIONS":{"sslmode":os.environ.get("POSTGRES_SSLMODE","prefer")}}}
PASSWORD_HASHERS=["django.contrib.auth.hashers.Argon2PasswordHasher","django.contrib.auth.hashers.PBKDF2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS=[{"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator","OPTIONS":{"min_length":12}},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE="pt-br"; TIME_ZONE="America/Sao_Paulo"; USE_I18N=True; USE_TZ=True
STATIC_URL="static/"; STATIC_ROOT=BASE_DIR/"staticfiles"; STATICFILES_DIRS=[BASE_DIR/"static"]
MEDIA_URL="/arquivos/"; MEDIA_ROOT=BASE_DIR/"private_media"
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"; LOGIN_URL="/contas/entrar/"; LOGIN_REDIRECT_URL="/"; LOGOUT_REDIRECT_URL="/"
SESSION_COOKIE_AGE=int(os.environ.get("SESSION_COOKIE_AGE",str(8*60*60))); SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SESSION_COOKIE_HTTPONLY=True; SESSION_COOKIE_SAMESITE="Lax"; CSRF_COOKIE_SAMESITE="Lax"; X_FRAME_OPTIONS="DENY"; SECURE_CONTENT_TYPE_NOSNIFF=True
FILE_UPLOAD_MAX_MEMORY_SIZE=5*1024*1024; DATA_UPLOAD_MAX_MEMORY_SIZE=8*1024*1024
ENTRA_ENABLED=os.environ.get("ENTRA_ENABLED","False").lower()=="true"
ENTRA_TENANT_ID=os.environ.get("ENTRA_TENANT_ID",""); ENTRA_CLIENT_ID=os.environ.get("ENTRA_CLIENT_ID",""); ENTRA_CLIENT_SECRET=os.environ.get("ENTRA_CLIENT_SECRET","")
LOGGING={"version":1,"disable_existing_loggers":False,"formatters":{"verbose":{"format":"{asctime} {levelname} {name} {message}","style":"{"}},"handlers":{"console":{"class":"logging.StreamHandler","formatter":"verbose"}},"root":{"handlers":["console"],"level":os.environ.get("LOG_LEVEL","INFO")}}

# Bloqueio de login por tentativas (django-axes): 5 erros por usuário+IP bloqueiam por 15 minutos.
AXES_FAILURE_LIMIT=int(os.environ.get("AXES_FAILURE_LIMIT","5"))
AXES_COOLOFF_TIME=0.25
AXES_LOCKOUT_PARAMETERS=[["username","ip_address"]]
AXES_RESET_ON_SUCCESS=True
AXES_LOCKOUT_TEMPLATE="accounts/bloqueado.html"
# MFA (TOTP) obrigatório para estes perfis e para qualquer usuário com acesso ao /admin/.
OTP_TOTP_ISSUER="SIGA Coop"
SIGA_MFA_PERFIS=["Administrador"]

# API usada pelo app React (mesma origem, sessão do Django + CSRF; sem token no navegador).
REST_FRAMEWORK={
 "DEFAULT_AUTHENTICATION_CLASSES":["rest_framework.authentication.SessionAuthentication"],
 "DEFAULT_PERMISSION_CLASSES":["apps.core.drf.UsuarioVerificado"],
 "DEFAULT_RENDERER_CLASSES":["rest_framework.renderers.JSONRenderer"],
 "DEFAULT_PARSER_CLASSES":["rest_framework.parsers.JSONParser"],
 "DEFAULT_THROTTLE_CLASSES":["rest_framework.throttling.UserRateThrottle"],
 "DEFAULT_THROTTLE_RATES":{"user":os.environ.get("API_RATE","600/min")},
 "EXCEPTION_HANDLER":"apps.core.drf.tratar_excecao",
}
# App React compilado (frontend/dist). Servido pelo Django só para usuários logados.
SPA_DIR=BASE_DIR/"frontend"/"dist"
if (SPA_DIR/"assets").exists():
 STATICFILES_DIRS=[*STATICFILES_DIRS,("app/assets",SPA_DIR/"assets")]
