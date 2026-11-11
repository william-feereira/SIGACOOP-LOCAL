from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core.access import filtrar_por_unidade

from .models import TravelRequest


@login_required
def index(request):
    itens = filtrar_por_unidade(TravelRequest.objects.select_related("unit"), request.user, campo="unit", dono="requester")
    return render(request, "generic/module.html", {"title": "Viagens e reembolsos", "items": itens, "empty": "Nenhuma viagem cadastrada."})
