"""Reformas dos pontos de atendimento (PAs) com quadro Kanban de ações.

O diário (`RegistroAndamento`) é somente inserção: ninguém edita nem apaga o que foi registrado.
Mudanças de coluna, passagem de bastão e bloqueio só acontecem pelas funções de `servicos.py`.
"""
from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.contracts.models import Supplier
from apps.core.models import TimeStampedModel, Unit


class Reforma(TimeStampedModel):
    class Situacao(models.TextChoices):
        PLANEJADA = "PLANEJADA", "Planejada"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        PAUSADA = "PAUSADA", "Pausada"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        CANCELADA = "CANCELADA", "Cancelada"

    codigo = models.CharField(max_length=20, unique=True, editable=False)
    unidade = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="reformas", verbose_name="PA")
    titulo = models.CharField("título", max_length=160)
    objetivo = models.TextField(blank=True)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="reformas_responsavel", verbose_name="responsável interno")
    inicio = models.DateField("início", null=True, blank=True)
    fim_previsto = models.DateField("previsão de término", null=True, blank=True)
    situacao = models.CharField("situação", max_length=20, choices=Situacao.choices, default=Situacao.PLANEJADA)
    orcamento = models.DecimalField("orçamento aprovado", max_digits=14, decimal_places=2, null=True, blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(fim_previsto__isnull=True) | Q(inicio__isnull=True) | Q(fim_previsto__gte=F("inicio")),
                                   name="reforma_fim_apos_inicio"),
            models.CheckConstraint(condition=Q(orcamento__isnull=True) | Q(orcamento__gte=0), name="reforma_orcamento_positivo"),
        ]
        indexes = [models.Index(fields=["unidade", "situacao"])]

    def __str__(self):
        return f"{self.codigo} · {self.titulo}"


class Coluna(models.TextChoices):
    A_FAZER = "A_FAZER", "A fazer"
    EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
    BLOQUEADA = "BLOQUEADA", "Pausada/Bloqueada"
    VALIDACAO = "VALIDACAO", "Em validação"
    CONCLUIDA = "CONCLUIDA", "Concluída"


class Prioridade(models.TextChoices):
    BAIXA = "BAIXA", "Baixa"
    NORMAL = "NORMAL", "Normal"
    ALTA = "ALTA", "Alta"
    URGENTE = "URGENTE", "Urgente"


class AcaoReforma(TimeStampedModel):
    reforma = models.ForeignKey(Reforma, on_delete=models.PROTECT, related_name="acoes")
    titulo = models.CharField("o que fazer", max_length=160)
    descricao = models.TextField("detalhes", blank=True)
    coluna = models.CharField(max_length=20, choices=Coluna.choices, default=Coluna.A_FAZER)
    posicao = models.PositiveIntegerField(default=0)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="acoes_reforma", verbose_name="colaborador responsável")
    fornecedor = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name="acoes_reforma", verbose_name="terceiro (fornecedor)")
    prazo = models.DateField(null=True, blank=True)
    prioridade = models.CharField(max_length=10, choices=Prioridade.choices, default=Prioridade.NORMAL)
    depende_de = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="dependentes",
                                   verbose_name="só começa depois de")
    motivo_bloqueio = models.TextField("motivo da pausa/bloqueio", blank=True)
    iniciada_em = models.DateTimeField(null=True, blank=True)
    concluida_em = models.DateTimeField(null=True, blank=True)
    custo_previsto = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    custo_realizado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    versao = models.PositiveIntegerField(default=1, help_text="Controle de concorrência: muda a cada alteração.")
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")

    class Meta:
        verbose_name = "ação de reforma"
        verbose_name_plural = "ações de reforma"
        ordering = ["reforma", "coluna", "posicao", "id"]
        indexes = [models.Index(fields=["reforma", "coluna", "posicao"]), models.Index(fields=["responsavel", "coluna"])]
        constraints = [
            models.CheckConstraint(condition=~Q(coluna="BLOQUEADA") | ~Q(motivo_bloqueio=""), name="acao_bloqueada_tem_motivo"),
            models.CheckConstraint(condition=~Q(coluna="CONCLUIDA") | Q(concluida_em__isnull=False), name="acao_concluida_tem_data"),
            models.CheckConstraint(condition=Q(custo_previsto__isnull=True) | Q(custo_previsto__gte=0), name="acao_custo_previsto_positivo"),
            models.CheckConstraint(condition=Q(custo_realizado__isnull=True) | Q(custo_realizado__gte=0), name="acao_custo_realizado_positivo"),
            models.CheckConstraint(condition=Q(depende_de__isnull=True) | ~Q(depende_de=F("id")), name="acao_nao_depende_de_si"),
        ]

    def __str__(self):
        return self.titulo

    @property
    def quem_faz(self) -> str:
        if self.fornecedor_id and self.responsavel_id:
            return f"{self.fornecedor} (acompanha: {self.responsavel.get_full_name() or self.responsavel})"
        if self.fornecedor_id:
            return str(self.fornecedor)
        if self.responsavel_id:
            return self.responsavel.get_full_name() or str(self.responsavel)
        return "Sem responsável"


class RegistroAndamento(models.Model):
    """Diário imutável da ação: "comecei", "fiz", "parei em", "passei para"."""

    class Tipo(models.TextChoices):
        CRIACAO = "CRIACAO", "Ação criada"
        NOTA = "NOTA", "Anotação"
        PROGRESSO = "PROGRESSO", "Andamento"
        MOVIMENTO = "MOVIMENTO", "Mudou de coluna"
        INICIO = "INICIO", "Começou"
        BLOQUEIO = "BLOQUEIO", "Pausou/bloqueou"
        PASSAGEM = "PASSAGEM", "Passou adiante"
        CONCLUSAO = "CONCLUSAO", "Concluiu"

    reforma = models.ForeignKey(Reforma, on_delete=models.PROTECT, related_name="registros")
    acao = models.ForeignKey(AcaoReforma, on_delete=models.PROTECT, related_name="registros")
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    texto = models.TextField("o que foi feito / observação", blank=True)
    o_que_falta = models.TextField(blank=True)
    de_coluna = models.CharField(max_length=20, choices=Coluna.choices, blank=True)
    para_coluna = models.CharField(max_length=20, choices=Coluna.choices, blank=True)
    passado_para_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    passado_para_fornecedor = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "registro de andamento"
        verbose_name_plural = "registros de andamento"
        ordering = ["-criado_em", "-id"]
        indexes = [models.Index(fields=["acao", "-criado_em"]), models.Index(fields=["reforma", "-criado_em"])]

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Registros de andamento não podem ser alterados.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Registros de andamento não podem ser apagados.")


class ItemChecklist(TimeStampedModel):
    acao = models.ForeignKey(AcaoReforma, on_delete=models.CASCADE, related_name="checklist")
    texto = models.CharField(max_length=200)
    feito = models.BooleanField(default=False)
    feito_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    feito_em = models.DateTimeField(null=True, blank=True)
    posicao = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["posicao", "id"]
        constraints = [models.CheckConstraint(condition=Q(feito=False) | Q(feito_em__isnull=False), name="checklist_feito_tem_data")]


class MembroReforma(TimeStampedModel):
    """Quem participa da reforma além do gestor da unidade (ex.: equipe de patrimônio de outra sede)."""

    class Papel(models.TextChoices):
        RESPONSAVEL = "RESPONSAVEL", "Responsável"
        COLABORADOR = "COLABORADOR", "Colaborador (edita)"
        LEITOR = "LEITOR", "Acompanha (só leitura)"

    reforma = models.ForeignKey(Reforma, on_delete=models.CASCADE, related_name="membros")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reformas_membro")
    papel = models.CharField(max_length=12, choices=Papel.choices, default=Papel.COLABORADOR)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["reforma", "usuario"], name="membro_reforma_unico")]
