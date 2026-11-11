"""Regras do Kanban de reformas. Toda escrita passa por aqui, em transação, com auditoria.

As telas (Django ou API) só chamam estas funções: elas conferem permissão, versão e transição.
"""
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Count, Max, Q, QuerySet
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.core.access import filtrar_por_unidade, pode_gerir_unidade, pode_ver_unidade

from .models import AcaoReforma, Coluna, ItemChecklist, MembroReforma, Reforma, RegistroAndamento

Tipo = RegistroAndamento.Tipo
EDITORES = (MembroReforma.Papel.RESPONSAVEL, MembroReforma.Papel.COLABORADOR)


class RegraDeNegocio(Exception):
    """Ação recusada por regra de negócio. A mensagem é mostrada ao usuário."""


class SemPermissao(RegraDeNegocio):
    pass


class ConflitoDeVersao(RegraDeNegocio):
    def __init__(self):
        super().__init__("Outra pessoa alterou esta ação agora há pouco. Recarregue para ver a versão atual.")


# ---------- Permissões ----------

def reformas_visiveis(user) -> QuerySet:
    base = Reforma.objects.select_related("unidade", "responsavel")
    por_unidade = filtrar_por_unidade(base, user, campo="unidade").values("pk")
    return base.filter(Q(pk__in=por_unidade) | Q(membros__usuario=user)).distinct()


def pode_ver(user, reforma: Reforma) -> bool:
    return pode_ver_unidade(user, reforma.unidade_id) or reforma.membros.filter(usuario=user).exists()


def pode_editar(user, reforma: Reforma) -> bool:
    if reforma.situacao in (Reforma.Situacao.CONCLUIDA, Reforma.Situacao.CANCELADA):
        return False
    return pode_gerir_unidade(user, reforma.unidade_id) or reforma.membros.filter(usuario=user, papel__in=EDITORES).exists()


def _exigir_edicao(user, reforma):
    if not pode_editar(user, reforma):
        raise SemPermissao("Você não pode alterar esta reforma.")


def _auditar(user, acao: str, obj, **detalhes):
    AuditEvent.objects.create(actor=user, module="reformas", action=acao, object_type=type(obj).__name__,
                              object_id=str(obj.pk), details=detalhes)


# ---------- Reforma ----------

def _proximo_codigo() -> str:
    ano = timezone.localdate().year
    ultimo = Reforma.objects.select_for_update().filter(codigo__startswith=f"REF-{ano}-").order_by("-codigo").first()
    numero = int(ultimo.codigo.rsplit("-", 1)[1]) + 1 if ultimo else 1
    return f"REF-{ano}-{numero:03d}"


@transaction.atomic
def criar_reforma(user, **dados) -> Reforma:
    unidade = dados["unidade"]
    if not pode_gerir_unidade(user, unidade.pk):
        raise SemPermissao("Só gestores do PA ou administradores podem abrir uma reforma.")
    reforma = Reforma(criado_por=user, **dados)
    reforma.codigo = _proximo_codigo()
    reforma.full_clean()
    reforma.save()
    if reforma.responsavel_id:
        MembroReforma.objects.get_or_create(reforma=reforma, usuario=reforma.responsavel,
                                            defaults={"papel": MembroReforma.Papel.RESPONSAVEL})
    _auditar(user, "reforma_criada", reforma, unidade=unidade.pk)
    return reforma


def progresso(reforma: Reforma) -> dict:
    total = reforma.acoes.aggregate(
        total=Count("id"), concluidas=Count("id", filter=Q(coluna=Coluna.CONCLUIDA)),
        bloqueadas=Count("id", filter=Q(coluna=Coluna.BLOQUEADA)),
        atrasadas=Count("id", filter=Q(prazo__lt=timezone.localdate()) & ~Q(coluna=Coluna.CONCLUIDA)))
    total["percentual"] = round(100 * total["concluidas"] / total["total"]) if total["total"] else 0
    return total


# ---------- Ações (cartões) ----------

def _fim_da_coluna(reforma_id, coluna) -> int:
    ultimo = AcaoReforma.objects.filter(reforma_id=reforma_id, coluna=coluna).aggregate(m=Max("posicao"))["m"]
    return 0 if ultimo is None else ultimo + 1


@transaction.atomic
def criar_acao(user, reforma: Reforma, **dados) -> AcaoReforma:
    _exigir_edicao(user, reforma)
    depende_de = dados.get("depende_de")
    if depende_de and depende_de.reforma_id != reforma.pk:
        raise RegraDeNegocio("A dependência precisa ser uma ação da mesma reforma.")
    acao = AcaoReforma(reforma=reforma, criado_por=user, coluna=Coluna.A_FAZER,
                       posicao=_fim_da_coluna(reforma.pk, Coluna.A_FAZER), **dados)
    acao.full_clean()
    acao.save()
    RegistroAndamento.objects.create(reforma=reforma, acao=acao, tipo=Tipo.CRIACAO, autor=user,
                                     para_coluna=acao.coluna, texto=acao.descricao)
    _auditar(user, "acao_criada", acao, reforma=reforma.pk)
    return acao


def _travar(user, acao_id, versao_esperada) -> AcaoReforma:
    acao = AcaoReforma.objects.select_for_update().select_related("reforma").get(pk=acao_id)
    _exigir_edicao(user, acao.reforma)
    if versao_esperada is not None and acao.versao != versao_esperada:
        raise ConflitoDeVersao()
    return acao


def _gravar(acao: AcaoReforma, campos: list[str]):
    acao.versao += 1
    acao.full_clean()
    acao.save(update_fields=[*campos, "versao", "updated_at"])


TIPO_POR_COLUNA = {
    Coluna.EM_ANDAMENTO: Tipo.INICIO, Coluna.BLOQUEADA: Tipo.BLOQUEIO, Coluna.CONCLUIDA: Tipo.CONCLUSAO,
}


@transaction.atomic
def mover_acao(user, acao_id, para_coluna: str, *, versao_esperada: int | None, posicao: int | None = None,
               texto: str = "", motivo_bloqueio: str = "") -> AcaoReforma:
    acao = _travar(user, acao_id, versao_esperada)
    if para_coluna not in Coluna.values:
        raise RegraDeNegocio("Coluna inválida.")
    de_coluna = acao.coluna
    motivo_bloqueio = motivo_bloqueio.strip()
    if para_coluna == Coluna.BLOQUEADA and not motivo_bloqueio:
        raise RegraDeNegocio("Informe o motivo da pausa ou do bloqueio.")
    if para_coluna in (Coluna.EM_ANDAMENTO, Coluna.VALIDACAO, Coluna.CONCLUIDA) and acao.depende_de_id \
            and acao.depende_de.coluna != Coluna.CONCLUIDA:
        raise RegraDeNegocio(f"Esta ação depende de \"{acao.depende_de}\", que ainda não foi concluída.")

    agora = timezone.now()
    acao.coluna = para_coluna
    acao.motivo_bloqueio = motivo_bloqueio if para_coluna == Coluna.BLOQUEADA else ""
    if para_coluna == Coluna.EM_ANDAMENTO and not acao.iniciada_em:
        acao.iniciada_em = agora
    acao.concluida_em = agora if para_coluna == Coluna.CONCLUIDA else None

    irmas = list(AcaoReforma.objects.select_for_update().filter(reforma_id=acao.reforma_id, coluna=para_coluna)
                 .exclude(pk=acao.pk).order_by("posicao", "id"))
    destino = len(irmas) if posicao is None else max(0, min(posicao, len(irmas)))
    irmas.insert(destino, acao)
    for i, item in enumerate(irmas):
        if item.pk != acao.pk and item.posicao != i:
            AcaoReforma.objects.filter(pk=item.pk).update(posicao=i)
    acao.posicao = destino
    _gravar(acao, ["coluna", "posicao", "motivo_bloqueio", "iniciada_em", "concluida_em"])

    if de_coluna != para_coluna:
        RegistroAndamento.objects.create(
            reforma_id=acao.reforma_id, acao=acao, autor=user, tipo=TIPO_POR_COLUNA.get(para_coluna, Tipo.MOVIMENTO),
            de_coluna=de_coluna, para_coluna=para_coluna, texto=motivo_bloqueio or texto.strip())
        _auditar(user, "acao_movida", acao, de=de_coluna, para=para_coluna)
        _atualizar_situacao_reforma(acao.reforma)
    return acao


def _atualizar_situacao_reforma(reforma: Reforma):
    """Reforma planejada vira "em andamento" quando a primeira ação começa."""
    if reforma.situacao == Reforma.Situacao.PLANEJADA and reforma.acoes.exclude(coluna=Coluna.A_FAZER).exists():
        Reforma.objects.filter(pk=reforma.pk).update(situacao=Reforma.Situacao.EM_ANDAMENTO, updated_at=timezone.now())


@transaction.atomic
def registrar_andamento(user, acao_id, texto: str, *, tipo: str = Tipo.PROGRESSO) -> RegistroAndamento:
    if tipo not in (Tipo.NOTA, Tipo.PROGRESSO):
        raise RegraDeNegocio("Use os botões de mover, bloquear ou passar adiante para os demais registros.")
    texto = texto.strip()
    if not texto:
        raise RegraDeNegocio("Escreva o que foi feito ou observado.")
    acao = _travar(user, acao_id, None)
    registro = RegistroAndamento.objects.create(reforma_id=acao.reforma_id, acao=acao, autor=user, tipo=tipo, texto=texto)
    _auditar(user, "andamento_registrado", acao, tipo=tipo)
    return registro


@dataclass
class Passagem:
    feito: str
    o_que_falta: str
    para_usuario: object = None
    para_fornecedor: object = None


@transaction.atomic
def passar_adiante(user, acao_id, passagem: Passagem, *, versao_esperada: int | None) -> AcaoReforma:
    """Registra o que foi feito e o que falta, e troca quem continua a ação."""
    acao = _travar(user, acao_id, versao_esperada)
    if acao.coluna == Coluna.CONCLUIDA:
        raise RegraDeNegocio("A ação já foi concluída.")
    feito, falta = passagem.feito.strip(), passagem.o_que_falta.strip()
    if not feito or not falta:
        raise RegraDeNegocio("Conte o que foi feito e o que falta para quem vai continuar.")
    if not passagem.para_usuario and not passagem.para_fornecedor:
        raise RegraDeNegocio("Escolha quem vai continuar: um colaborador ou um terceiro.")
    acao.responsavel = passagem.para_usuario or acao.responsavel
    acao.fornecedor = passagem.para_fornecedor
    _gravar(acao, ["responsavel", "fornecedor"])
    RegistroAndamento.objects.create(
        reforma_id=acao.reforma_id, acao=acao, autor=user, tipo=Tipo.PASSAGEM, texto=feito, o_que_falta=falta,
        passado_para_usuario=passagem.para_usuario, passado_para_fornecedor=passagem.para_fornecedor)
    _auditar(user, "acao_passada_adiante", acao,
             usuario=getattr(passagem.para_usuario, "pk", None), fornecedor=getattr(passagem.para_fornecedor, "pk", None))
    return acao


@transaction.atomic
def marcar_item(user, item_id, feito: bool) -> ItemChecklist:
    item = ItemChecklist.objects.select_for_update().select_related("acao__reforma").get(pk=item_id)
    _exigir_edicao(user, item.acao.reforma)
    item.feito = feito
    item.feito_por = user if feito else None
    item.feito_em = timezone.now() if feito else None
    item.save(update_fields=["feito", "feito_por", "feito_em", "updated_at"])
    return item


@transaction.atomic
def adicionar_item(user, acao_id, texto: str) -> ItemChecklist:
    acao = _travar(user, acao_id, None)
    texto = texto.strip()
    if not texto:
        raise RegraDeNegocio("Escreva o item do checklist.")
    ultimo = acao.checklist.aggregate(m=Max("posicao"))["m"]
    return ItemChecklist.objects.create(acao=acao, texto=texto, posicao=0 if ultimo is None else ultimo + 1)
