"""Base da API: permissão padrão, tratamento de erros e dados do usuário logado."""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.mfa import exige_mfa
from apps.core.access import pode_gerir_unidade, perfis, tem_perfil, unidades_ids, ve_todas_unidades, ADMINISTRADOR
from apps.core.models import Unit


class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "code", "name"]


@method_decorator(ensure_csrf_cookie, name="dispatch")
class EuView(APIView):
    """Quem está logado, perfis e unidades. Também entrega o cookie CSRF ao app."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        unidades = Unit.objects.filter(active=True).order_by("code")
        if not ve_todas_unidades(user):
            unidades = unidades.filter(pk__in=unidades_ids(user))
        return Response({
            "id": user.pk, "usuario": user.get_username(), "nome": user.get_full_name() or user.get_username(),
            "perfis": sorted(perfis(user)), "admin": tem_perfil(user, ADMINISTRADOR), "staff": user.is_staff,
            "mfa_pendente": exige_mfa(user) and not user.is_verified(),
            "unidades": [{**UnidadeSerializer(u).data, "pode_gerir": pode_gerir_unidade(user, u.pk)} for u in unidades],
            "permissoes": {
                "ativos": user.has_perm("assets.view_asset"), "frota": user.has_perm("fleet.view_vehicle"),
                "contratos": user.has_perm("contracts.view_contract"),
            },
            "logout": reverse("accounts:logout"),
        })


class PessoasView(APIView):
    """Colaboradores que podem receber uma ação: das mesmas unidades (Admin/Diretoria: todos)."""

    def get(self, request):
        User = get_user_model()
        qs = User.objects.filter(is_active=True)
        if not ve_todas_unidades(request.user):
            ids = unidades_ids(request.user)
            qs = qs.filter(siga_profile__unit_id__in=ids) | qs.filter(acessos_unidade__unidade_id__in=ids)
        qs = qs.distinct().order_by("first_name", "username")[:500]
        return Response([{"id": u.pk, "nome": u.get_full_name() or u.get_username()} for u in qs])
