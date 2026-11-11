from .access import perfis

# (seção, rótulo, caminho, ícone, permissão exigida ou None)
MENU = (
    ("Início", "Visão geral", "/", "house", None),
    ("Operação", "Reformas dos PAs", "/reformas", "hard-hat", None),
    ("Início", "Solicitações", "/solicitacoes/", "clipboard-list", None),
    ("Operação", "Ativos e patrimônio", "/ativos/", "boxes", "assets.view_asset"),
    ("Operação", "Frota", "/frota/", "car", "fleet.view_vehicle"),
    ("Operação", "Viagens", "/viagens/", "plane", None),
    ("Gestão", "Contratos e fornecedores", "/contratos/", "file-pen-line", "contracts.view_contract"),
    ("Gestão", "Indicadores", "/analytics/", "chart-column", None),
)


def navegacao(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    atual = request.path
    secoes: dict[str, list[dict]] = {}
    for secao, rotulo, caminho, icone, perm in MENU:
        if perm and not user.has_perm(perm):
            continue
        ativo = atual == caminho if caminho == "/" else atual.startswith(caminho)
        secoes.setdefault(secao, []).append({"rotulo": rotulo, "caminho": caminho, "icone": icone, "ativo": ativo})
    if user.is_staff:
        secoes.setdefault("Administração", []).append(
            {"rotulo": "Administração", "caminho": "/admin/", "icone": "settings", "ativo": atual.startswith("/admin/")})
    return {"menu": list(secoes.items()), "perfis_usuario": sorted(perfis(user))}
