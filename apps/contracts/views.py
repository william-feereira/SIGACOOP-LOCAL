from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from apps.core.access import filtrar_por_unidade

from .models import Contract


@login_required
@permission_required("contracts.view_contract", raise_exception=True)
def index(request):
    itens = filtrar_por_unidade(Contract.objects.select_related("supplier"), request.user, campo="units")
    return render(request, "generic/module.html", {"title": "Contratos e fornecedores", "items": itens, "empty": "Nenhum contrato cadastrado."})
