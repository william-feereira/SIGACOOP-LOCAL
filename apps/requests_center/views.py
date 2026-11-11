from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.models import AuditEvent
from apps.core.access import filtrar_por_unidade

from .forms import RequestForm
from .models import AdministrativeRequest, RequestEvent


def solicitacoes_visiveis(user):
    """Solicitante vê as próprias; Gestor, as das suas unidades; Admin e Diretoria, todas."""
    qs = AdministrativeRequest.objects.select_related("requester", "beneficiary_unit", "assigned_to")
    return filtrar_por_unidade(qs, user, campo="beneficiary_unit", dono="requester")


@login_required
def request_list(request):
    return render(request, "requests_center/list.html", {"items": solicitacoes_visiveis(request.user).order_by("-created_at")[:100]})


@login_required
def request_create(request):
    form = RequestForm(request.POST or None)
    if form.is_valid():
        with transaction.atomic():
            obj = form.save(commit=False)
            obj.requester = request.user
            obj.status = AdministrativeRequest.Status.PENDING
            obj.save()
            RequestEvent.objects.create(request=obj, actor=request.user, action="Solicitação enviada", to_status=obj.status)
            AuditEvent.objects.create(actor=request.user, module="requests_center", action="request_created",
                                      object_type="AdministrativeRequest", object_id=str(obj.pk), details={"status": obj.status})
        return redirect("requests_center:detail", pk=obj.pk)
    return render(request, "requests_center/form.html", {"form": form})


@login_required
def request_detail(request, pk):
    # 404 (e não 403) para não revelar que o registro existe em outra unidade.
    obj = get_object_or_404(solicitacoes_visiveis(request.user), pk=pk)
    return render(request, "requests_center/detail.html", {"item": obj})
