from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from apps.core.access import filtrar_por_unidade

from .models import Vehicle


@login_required
@permission_required("fleet.view_vehicle", raise_exception=True)
def index(request):
    itens = filtrar_por_unidade(Vehicle.objects.select_related("unit"), request.user, campo="unit")
    return render(request, "generic/module.html", {"title": "Frota", "items": itens, "empty": "Nenhum veículo cadastrado."})
