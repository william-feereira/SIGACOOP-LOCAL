from django.urls import path

from . import api

urlpatterns = [
    path("reformas/", api.ReformasView.as_view()),
    path("reformas/<int:pk>/", api.ReformaView.as_view()),
    path("reformas/<int:pk>/linha-do-tempo/", api.LinhaDoTempoView.as_view()),
    path("reformas/<int:pk>/acoes/", api.AcoesView.as_view()),
    path("acoes/<int:pk>/", api.AcaoView.as_view()),
    path("acoes/<int:pk>/mover/", api.MoverView.as_view()),
    path("acoes/<int:pk>/andamento/", api.AndamentoView.as_view()),
    path("acoes/<int:pk>/passar/", api.PassarView.as_view()),
    path("acoes/<int:pk>/checklist/", api.ChecklistView.as_view()),
    path("checklist/<int:pk>/", api.ItemView.as_view()),
    path("fornecedores/", api.FornecedoresView.as_view()),
    path("painel/", api.PainelView.as_view()),
]
