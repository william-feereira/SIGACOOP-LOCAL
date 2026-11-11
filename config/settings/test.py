import os
os.environ.setdefault("SECRET_KEY", "test-only-not-for-production")
from .base import *  # noqa: E402,F403
# Testes rodam no PostgreSQL (mesmo banco de produção), a menos que DB_ENGINE=sqlite.
PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES={"default":{"BACKEND":"django.core.files.storage.FileSystemStorage"},"staticfiles":{"BACKEND":"django.contrib.staticfiles.storage.StaticFilesStorage"}}
WHITENOISE_AUTOREFRESH=True
