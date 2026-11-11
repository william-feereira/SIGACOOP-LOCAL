from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.requests_center.views import solicitacoes_visiveis

FINALIZADAS = ["DONE", "CANCELLED", "REJECTED"]


@login_required
def home(request):
    qs = solicitacoes_visiveis(request.user)
    return render(request, "core/home.html", {
        "open_count": qs.exclude(status__in=FINALIZADAS).count(),
        "recent": qs.order_by("-created_at")[:6],
    })
