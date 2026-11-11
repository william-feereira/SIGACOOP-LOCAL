from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from apps.core.access import filtrar_por_unidade
from apps.requests_center.views import solicitacoes_visiveis
from apps.travels.models import TravelRequest


@login_required
def dashboard(request):
    req = solicitacoes_visiveis(request.user)
    travels = filtrar_por_unidade(TravelRequest.objects.all(), request.user, campo="unit", dono="requester")
    return render(request, "analytics/dashboard.html", {
        "total_requests": req.count(),
        "pending": req.exclude(status__in=["DONE", "REJECTED", "CANCELLED"]).count(),
        "estimated": req.aggregate(v=Sum("estimated_value"))["v"] or 0,
        "travel_total": travels.aggregate(v=Sum("reimbursement"))["v"] or 0,
    })
