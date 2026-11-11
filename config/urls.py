from django.contrib import admin
from django.urls import include, path, re_path

from apps.core.api import EuView, PessoasView
from apps.core.spa import app

api = [
    path("eu/", EuView.as_view()),
    path("pessoas/", PessoasView.as_view()),
    path("", include("apps.reformas.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api)),
    path("", include("apps.core.urls")),
    path("contas/", include("apps.accounts.urls")),
    path("solicitacoes/", include("apps.requests_center.urls")),
    path("frota/", include("apps.fleet.urls")),
    path("viagens/", include("apps.travels.urls")),
    path("ativos/", include("apps.assets.urls")),
    path("contratos/", include("apps.contracts.urls")),
    path("analytics/", include("apps.analytics.urls")),
    # Telas do app React (o roteamento fica no navegador).
    path("", app, name="app"),
    re_path(r"^(?P<caminho>(painel|reformas)(/.*)?)$", app),
]
