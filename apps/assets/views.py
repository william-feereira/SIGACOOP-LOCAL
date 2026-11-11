from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from apps.core.access import filtrar_por_unidade

from .models import Asset


@login_required
@permission_required("assets.view_asset", raise_exception=True)
def index(request):
    itens = filtrar_por_unidade(Asset.objects.select_related("unit"), request.user, campo="unit")
    return render(request, "generic/module.html", {"title": "Ativos e patrimônio", "items": itens, "empty": "Nenhum ativo cadastrado."})
