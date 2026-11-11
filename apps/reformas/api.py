"""API do Kanban de reformas. Toda escrita chama `servicos.py`; aqui só há validação de entrada e formato."""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.contracts.models import Supplier
from apps.core.models import Unit

from . import servicos as s
from .models import AcaoReforma, Coluna, ItemChecklist, Prioridade, Reforma, RegistroAndamento

User = get_user_model()


def _pessoa(u):
    return {"id": u.pk, "nome": u.get_full_name() or u.get_username()} if u else None


def _fornecedor(f):
    return {"id": f.pk, "nome": f.name, "especialidade": f.especialidade} if f else None


# ---------- Leitura ----------

def acao_json(a: AcaoReforma) -> dict:
    return {
        "id": a.pk, "titulo": a.titulo, "descricao": a.descricao, "coluna": a.coluna, "posicao": a.posicao,
        "prioridade": a.prioridade, "prazo": a.prazo, "atrasada": bool(a.prazo and a.prazo < timezone.localdate() and a.coluna != Coluna.CONCLUIDA),
        "responsavel": _pessoa(a.responsavel), "fornecedor": _fornecedor(a.fornecedor), "quem_faz": a.quem_faz,
        "depende_de": {"id": a.depende_de_id, "titulo": a.depende_de.titulo, "coluna": a.depende_de.coluna} if a.depende_de_id else None,
        "motivo_bloqueio": a.motivo_bloqueio, "versao": a.versao,
        "checklist_total": getattr(a, "n_check", None), "checklist_feitos": getattr(a, "n_feitos", None),
    }


def registro_json(r: RegistroAndamento) -> dict:
    return {
        "id": r.pk, "tipo": r.tipo, "tipo_rotulo": r.get_tipo_display(), "texto": r.texto, "o_que_falta": r.o_que_falta,
        "de_coluna": r.de_coluna, "para_coluna": r.para_coluna, "autor": _pessoa(r.autor), "criado_em": r.criado_em,
        "passado_para": _pessoa(r.passado_para_usuario) or _fornecedor(r.passado_para_fornecedor),
        "acao": {"id": r.acao_id, "titulo": r.acao.titulo},
    }


def reforma_json(r: Reforma, user) -> dict:
    return {
        "id": r.pk, "codigo": r.codigo, "titulo": r.titulo, "objetivo": r.objetivo, "situacao": r.situacao,
        "situacao_rotulo": r.get_situacao_display(), "unidade": {"id": r.unidade_id, "code": r.unidade.code, "name": r.unidade.name},
        "responsavel": _pessoa(r.responsavel), "inicio": r.inicio, "fim_previsto": r.fim_previsto,
        "orcamento": r.orcamento, "progresso": s.progresso(r), "pode_editar": s.pode_editar(user, r),
    }


class ReformasView(APIView):
    def get(self, request):
        qs = s.reformas_visiveis(request.user)
        if request.query_params.get("unidade"):
            qs = qs.filter(unidade_id=request.query_params["unidade"])
        if request.query_params.get("situacao"):
            qs = qs.filter(situacao=request.query_params["situacao"])
        return Response([reforma_json(r, request.user) for r in qs[:200]])

    @method_decorator(transaction.atomic)
    def post(self, request):
        dados = NovaReformaSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        reforma = s.criar_reforma(request.user, **dados.validated_data)
        modelo = request.data.get("acoes_iniciais") or []
        if not isinstance(modelo, list):
            modelo = []
        for titulo in [t.strip()[:160] for t in modelo if isinstance(t, str) and t.strip()][:40]:
            s.criar_acao(request.user, reforma, titulo=titulo)
        return Response(reforma_json(reforma, request.user), status=status.HTTP_201_CREATED)


def _reforma_visivel(user, pk) -> Reforma:
    return get_object_or_404(s.reformas_visiveis(user), pk=pk)


def _acoes(reforma):
    return (reforma.acoes.select_related("responsavel", "fornecedor", "depende_de")
            .annotate(n_check=Count("checklist", distinct=True), n_feitos=Count("checklist", filter=Q(checklist__feito=True), distinct=True))
            .order_by("coluna", "posicao", "id"))


class ReformaView(APIView):
    def get(self, request, pk):
        reforma = _reforma_visivel(request.user, pk)
        return Response({**reforma_json(reforma, request.user),
                         "colunas": [{"id": c.value, "rotulo": c.label} for c in Coluna],
                         "acoes": [acao_json(a) for a in _acoes(reforma)]})


class LinhaDoTempoView(APIView):
    def get(self, request, pk):
        reforma = _reforma_visivel(request.user, pk)
        regs = reforma.registros.select_related("autor", "acao", "passado_para_usuario", "passado_para_fornecedor")[:300]
        return Response([registro_json(r) for r in regs])


# ---------- Escrita ----------

class NovaReformaSerializer(serializers.Serializer):
    unidade = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.filter(active=True))
    titulo = serializers.CharField(max_length=160)
    objetivo = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    responsavel = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), required=False, allow_null=True)
    inicio = serializers.DateField(required=False, allow_null=True)
    fim_previsto = serializers.DateField(required=False, allow_null=True)
    orcamento = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=0)


class NovaAcaoSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=160)
    descricao = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    responsavel = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), required=False, allow_null=True)
    fornecedor = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.filter(active=True), required=False, allow_null=True)
    prazo = serializers.DateField(required=False, allow_null=True)
    prioridade = serializers.ChoiceField(choices=Prioridade.choices, required=False)
    depende_de = serializers.PrimaryKeyRelatedField(queryset=AcaoReforma.objects.all(), required=False, allow_null=True)


class AcoesView(APIView):
    def post(self, request, pk):
        reforma = _reforma_visivel(request.user, pk)
        dados = NovaAcaoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        acao = s.criar_acao(request.user, reforma, **{k: v for k, v in dados.validated_data.items() if v is not None})
        return Response(acao_json(acao), status=status.HTTP_201_CREATED)


def _acao_visivel(user, pk) -> AcaoReforma:
    acao = get_object_or_404(AcaoReforma.objects.select_related("reforma", "responsavel", "fornecedor", "depende_de"), pk=pk)
    if not s.pode_ver(user, acao.reforma):
        from django.http import Http404
        raise Http404
    return acao


class AcaoView(APIView):
    def get(self, request, pk):
        acao = _acao_visivel(request.user, pk)
        regs = acao.registros.select_related("autor", "acao", "passado_para_usuario", "passado_para_fornecedor")
        return Response({**acao_json(acao), "pode_editar": s.pode_editar(request.user, acao.reforma),
                         "reforma": {"id": acao.reforma_id, "codigo": acao.reforma.codigo, "titulo": acao.reforma.titulo},
                         "checklist": [{"id": i.pk, "texto": i.texto, "feito": i.feito, "feito_por": _pessoa(i.feito_por), "feito_em": i.feito_em}
                                       for i in acao.checklist.select_related("feito_por")],
                         "registros": [registro_json(r) for r in regs]})


class MoverSerializer(serializers.Serializer):
    coluna = serializers.ChoiceField(choices=Coluna.choices)
    versao = serializers.IntegerField(min_value=1)
    posicao = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    motivo_bloqueio = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    texto = serializers.CharField(required=False, allow_blank=True, max_length=4000)


class MoverView(APIView):
    def post(self, request, pk):
        _acao_visivel(request.user, pk)
        d = MoverSerializer(data=request.data)
        d.is_valid(raise_exception=True)
        v = d.validated_data
        acao = s.mover_acao(request.user, pk, v["coluna"], versao_esperada=v["versao"], posicao=v.get("posicao"),
                            texto=v.get("texto", ""), motivo_bloqueio=v.get("motivo_bloqueio", ""))
        return Response(acao_json(acao))


class AndamentoView(APIView):
    def post(self, request, pk):
        _acao_visivel(request.user, pk)
        texto = serializers.CharField(max_length=4000).run_validation(request.data.get("texto", ""))
        reg = s.registrar_andamento(request.user, pk, texto)
        return Response(registro_json(reg), status=status.HTTP_201_CREATED)


class PassarSerializer(serializers.Serializer):
    feito = serializers.CharField(max_length=4000)
    o_que_falta = serializers.CharField(max_length=4000)
    para_usuario = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), required=False, allow_null=True)
    para_fornecedor = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.filter(active=True), required=False, allow_null=True)
    versao = serializers.IntegerField(min_value=1)


class PassarView(APIView):
    def post(self, request, pk):
        _acao_visivel(request.user, pk)
        d = PassarSerializer(data=request.data)
        d.is_valid(raise_exception=True)
        v = d.validated_data
        acao = s.passar_adiante(request.user, pk, s.Passagem(v["feito"], v["o_que_falta"], v.get("para_usuario"), v.get("para_fornecedor")),
                                versao_esperada=v["versao"])
        return Response(acao_json(acao))


class ChecklistView(APIView):
    def post(self, request, pk):
        acao = _acao_visivel(request.user, pk)
        texto = serializers.CharField(max_length=200).run_validation(request.data.get("texto", ""))
        item = s.adicionar_item(request.user, acao.pk, texto)
        return Response({"id": item.pk, "texto": item.texto, "feito": False}, status=status.HTTP_201_CREATED)


class ItemView(APIView):
    def patch(self, request, pk):
        item = get_object_or_404(ItemChecklist.objects.select_related("acao__reforma"), pk=pk)
        if not s.pode_ver(request.user, item.acao.reforma):
            from django.http import Http404
            raise Http404
        item = s.marcar_item(request.user, pk, serializers.BooleanField().run_validation(request.data.get("feito")))
        return Response({"id": item.pk, "feito": item.feito, "feito_por": _pessoa(item.feito_por), "feito_em": item.feito_em})


class FornecedoresView(APIView):
    def get(self, request):
        return Response([_fornecedor(f) for f in Supplier.objects.filter(active=True).order_by("name")[:500]])


class PainelView(APIView):
    """Números da visão geral, respeitando o escopo do usuário."""

    def get(self, request):
        from apps.requests_center.views import solicitacoes_visiveis
        reformas = s.reformas_visiveis(request.user)
        acoes = AcaoReforma.objects.filter(reforma__in=reformas.values("pk"))
        hoje = timezone.localdate()
        minhas = acoes.filter(responsavel=request.user).exclude(coluna=Coluna.CONCLUIDA).select_related(
            "reforma", "responsavel", "fornecedor", "depende_de").order_by("prazo", "id")[:8]
        return Response({
            "solicitacoes_abertas": solicitacoes_visiveis(request.user).exclude(status__in=["DONE", "CANCELLED", "REJECTED"]).count(),
            "reformas_ativas": reformas.exclude(situacao__in=["CONCLUIDA", "CANCELADA"]).count(),
            "acoes_bloqueadas": acoes.filter(coluna=Coluna.BLOQUEADA).count(),
            "acoes_atrasadas": acoes.filter(prazo__lt=hoje).exclude(coluna=Coluna.CONCLUIDA).count(),
            "minhas_acoes": [{**acao_json(a), "reforma": {"id": a.reforma_id, "codigo": a.reforma.codigo, "titulo": a.reforma.titulo}} for a in minhas],
        })
