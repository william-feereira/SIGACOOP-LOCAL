"""Perfis e escopo por unidade (PA/agência).

Regra única usada por todas as telas: nenhuma consulta de dados por unidade
deve ser feita sem passar por `filtrar_por_unidade` ou `pode_ver_unidade`.
"""
from django.db.models import Q, QuerySet

ADMINISTRADOR = "Administrador"
GESTOR = "Gestor"
DIRETORIA = "Diretoria"
SOLICITANTE = "Solicitante"
PERFIS = (ADMINISTRADOR, GESTOR, DIRETORIA, SOLICITANTE)


def perfis(user) -> set[str]:
    if not getattr(user, "is_authenticated", False):
        return set()
    cache = getattr(user, "_siga_perfis", None)
    if cache is None:
        cache = set(user.groups.filter(name__in=PERFIS).values_list("name", flat=True))
        if user.is_superuser:
            cache.add(ADMINISTRADOR)
        user._siga_perfis = cache
    return cache


def tem_perfil(user, *nomes: str) -> bool:
    return bool(perfis(user) & set(nomes))


def ve_todas_unidades(user) -> bool:
    """Administrador e Diretoria enxergam todas as unidades."""
    return tem_perfil(user, ADMINISTRADOR, DIRETORIA)


def unidades_ids(user) -> set[int]:
    """Unidades do usuário: a unidade do perfil + acessos extras concedidos."""
    if not getattr(user, "is_authenticated", False):
        return set()
    cache = getattr(user, "_siga_unidades", None)
    if cache is None:
        from apps.accounts.models import AcessoUnidade, UserProfile
        cache = set(AcessoUnidade.objects.filter(usuario=user).values_list("unidade_id", flat=True))
        unidade = UserProfile.objects.filter(user=user).values_list("unit_id", flat=True).first()
        if unidade:
            cache.add(unidade)
        user._siga_unidades = cache
    return cache


def pode_ver_unidade(user, unidade_id) -> bool:
    return ve_todas_unidades(user) or unidade_id in unidades_ids(user)


def pode_gerir_unidade(user, unidade_id) -> bool:
    """Diretoria só consulta. Gestor gere as próprias unidades; Administrador, todas."""
    if tem_perfil(user, ADMINISTRADOR):
        return True
    return tem_perfil(user, GESTOR) and unidade_id in unidades_ids(user)


def filtrar_por_unidade(qs: QuerySet, user, campo: str = "unit", dono: str | None = None) -> QuerySet:
    """Restringe `qs` às unidades visíveis. `dono` inclui também registros criados pelo próprio usuário."""
    if ve_todas_unidades(user):
        return qs
    filtro = Q(**{f"{campo}__in": unidades_ids(user)}) if tem_perfil(user, GESTOR) else Q(pk__in=[])
    if dono:
        filtro |= Q(**{dono: user})
    return qs.filter(filtro).distinct()
