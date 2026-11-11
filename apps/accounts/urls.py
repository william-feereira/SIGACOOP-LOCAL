from django.urls import path

from .views import SigaLoginView, SigaLogoutView, mfa_configurar, mfa_verificar

app_name = "accounts"
urlpatterns = [
    path("entrar/", SigaLoginView.as_view(), name="login"),
    path("sair/", SigaLogoutView.as_view(), name="logout"),
    path("verificacao/configurar/", mfa_configurar, name="mfa_configurar"),
    path("verificacao/", mfa_verificar, name="mfa_verificar"),
]
