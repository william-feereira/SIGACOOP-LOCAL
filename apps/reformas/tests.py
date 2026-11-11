from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.audit.models import AuditEvent
from apps.contracts.models import Supplier
from apps.core.access import DIRETORIA, GESTOR, SOLICITANTE
from apps.core.models import Unit

from . import servicos as s
from .models import AcaoReforma, Coluna, ItemChecklist, MembroReforma, RegistroAndamento

User = get_user_model()


def usuario(nome, perfil=None, unidade=None):
    u = User.objects.create_user(nome, password="senha-de-teste-longa")
    if perfil:
        u.groups.add(Group.objects.get(name=perfil))
    if unidade:
        UserProfile.objects.filter(user=u).update(unit=unidade)
    return User.objects.get(pk=u.pk)


class Base(TestCase):
    def setUp(self):
        self.pa = Unit.objects.create(code="PA07", name="PA Jardim")
        self.outro_pa = Unit.objects.create(code="PA08", name="PA Lago")
        self.gestor = usuario("gestor", GESTOR, self.pa)
        self.eletrica = Supplier.objects.create(name="Elétrica Alfa", document="11.111.111/0001-11", especialidade="Elétrica")
        self.pintura = Supplier.objects.create(name="Pinturas Beta", document="22.222.222/0001-22", especialidade="Pintura")
        self.reforma = s.criar_reforma(self.gestor, unidade=self.pa, titulo="Reforma da recepção",
                                       inicio=date(2026, 11, 16), fim_previsto=date(2026, 12, 18))
        self.acao = s.criar_acao(self.gestor, self.reforma, titulo="Refazer quadro elétrico", fornecedor=self.eletrica)


class ReformaTests(Base):
    def test_codigo_sequencial_por_ano(self):
        outra = s.criar_reforma(self.gestor, unidade=self.pa, titulo="Fachada")
        self.assertRegex(self.reforma.codigo, r"^REF-\d{4}-001$")
        self.assertTrue(outra.codigo.endswith("-002"))

    def test_gestor_de_outro_pa_nao_abre_reforma(self):
        alheio = usuario("alheio", GESTOR, self.outro_pa)
        with self.assertRaises(s.SemPermissao):
            s.criar_reforma(alheio, unidade=self.pa, titulo="X")

    def test_fim_antes_do_inicio_e_recusado(self):
        with self.assertRaises(ValidationError):
            s.criar_reforma(self.gestor, unidade=self.pa, titulo="X", inicio=date(2026, 12, 1), fim_previsto=date(2026, 11, 1))

    def test_visibilidade(self):
        diretor = usuario("diretor", DIRETORIA)
        alheio = usuario("alheio", GESTOR, self.outro_pa)
        convidado = usuario("convidado", SOLICITANTE, self.outro_pa)
        MembroReforma.objects.create(reforma=self.reforma, usuario=convidado, papel=MembroReforma.Papel.LEITOR)
        self.assertIn(self.reforma, s.reformas_visiveis(diretor))
        self.assertNotIn(self.reforma, s.reformas_visiveis(alheio))
        self.assertIn(self.reforma, s.reformas_visiveis(convidado))
        self.assertFalse(s.pode_editar(diretor, self.reforma))
        self.assertFalse(s.pode_editar(convidado, self.reforma))

    def test_membro_colaborador_edita_mesmo_de_outro_pa(self):
        colaborador = usuario("patrimonio", SOLICITANTE, self.outro_pa)
        MembroReforma.objects.create(reforma=self.reforma, usuario=colaborador, papel=MembroReforma.Papel.COLABORADOR)
        s.registrar_andamento(colaborador, self.acao.pk, "Visitei o local e medi os circuitos.")

    def test_progresso_calculado(self):
        s.criar_acao(self.gestor, self.reforma, titulo="Pintar paredes", prazo=date.today() - timedelta(days=1))
        s.mover_acao(self.gestor, self.acao.pk, Coluna.CONCLUIDA, versao_esperada=None)
        p = s.progresso(self.reforma)
        self.assertEqual((p["total"], p["concluidas"], p["percentual"], p["atrasadas"]), (2, 1, 50, 1))


class KanbanTests(Base):
    def test_mover_registra_diario_auditoria_e_datas(self):
        acao = s.mover_acao(self.gestor, self.acao.pk, Coluna.EM_ANDAMENTO, versao_esperada=1)
        self.assertIsNotNone(acao.iniciada_em)
        self.assertEqual(acao.versao, 2)
        ultimo = acao.registros.first()
        self.assertEqual((ultimo.tipo, ultimo.de_coluna, ultimo.para_coluna), ("INICIO", "A_FAZER", "EM_ANDAMENTO"))
        self.assertTrue(AuditEvent.objects.filter(module="reformas", action="acao_movida").exists())
        self.reforma.refresh_from_db()
        self.assertEqual(self.reforma.situacao, "EM_ANDAMENTO")
        acao = s.mover_acao(self.gestor, acao.pk, Coluna.CONCLUIDA, versao_esperada=2)
        self.assertIsNotNone(acao.concluida_em)
        acao = s.mover_acao(self.gestor, acao.pk, Coluna.VALIDACAO, versao_esperada=3)
        self.assertIsNone(acao.concluida_em)

    def test_bloqueio_exige_motivo(self):
        with self.assertRaises(s.RegraDeNegocio):
            s.mover_acao(self.gestor, self.acao.pk, Coluna.BLOQUEADA, versao_esperada=1, motivo_bloqueio="  ")
        acao = s.mover_acao(self.gestor, self.acao.pk, Coluna.BLOQUEADA, versao_esperada=1,
                            motivo_bloqueio="Aguardando a concessionária desligar a energia")
        self.assertEqual(acao.registros.first().texto, "Aguardando a concessionária desligar a energia")
        acao = s.mover_acao(self.gestor, acao.pk, Coluna.EM_ANDAMENTO, versao_esperada=2)
        self.assertEqual(acao.motivo_bloqueio, "")

    def test_banco_recusa_bloqueio_sem_motivo(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            AcaoReforma.objects.filter(pk=self.acao.pk).update(coluna=Coluna.BLOQUEADA, motivo_bloqueio="")

    def test_conflito_de_versao(self):
        s.mover_acao(self.gestor, self.acao.pk, Coluna.EM_ANDAMENTO, versao_esperada=1)
        with self.assertRaises(s.ConflitoDeVersao):
            s.mover_acao(self.gestor, self.acao.pk, Coluna.VALIDACAO, versao_esperada=1)

    def test_dependencia_impede_comecar_antes(self):
        pintar = s.criar_acao(self.gestor, self.reforma, titulo="Pintar", fornecedor=self.pintura, depende_de=self.acao)
        with self.assertRaisesMessage(s.RegraDeNegocio, "Refazer quadro elétrico"):
            s.mover_acao(self.gestor, pintar.pk, Coluna.EM_ANDAMENTO, versao_esperada=1)
        s.mover_acao(self.gestor, self.acao.pk, Coluna.CONCLUIDA, versao_esperada=1)
        s.mover_acao(self.gestor, pintar.pk, Coluna.EM_ANDAMENTO, versao_esperada=1)

    def test_dependencia_de_outra_reforma_e_recusada(self):
        outra = s.criar_reforma(self.gestor, unidade=self.pa, titulo="Outra")
        with self.assertRaises(s.RegraDeNegocio):
            s.criar_acao(self.gestor, outra, titulo="X", depende_de=self.acao)

    def test_reordenar_na_coluna(self):
        b = s.criar_acao(self.gestor, self.reforma, titulo="B")
        c = s.criar_acao(self.gestor, self.reforma, titulo="C")
        s.mover_acao(self.gestor, c.pk, Coluna.A_FAZER, versao_esperada=1, posicao=0)
        ordem = list(self.reforma.acoes.filter(coluna=Coluna.A_FAZER).order_by("posicao").values_list("titulo", flat=True))
        self.assertEqual(ordem, ["C", "Refazer quadro elétrico", "B"])
        self.assertFalse(RegistroAndamento.objects.filter(acao=b, tipo="MOVIMENTO").exists())

    def test_quem_nao_edita_nao_move(self):
        diretor = usuario("diretor", DIRETORIA)
        with self.assertRaises(s.SemPermissao):
            s.mover_acao(diretor, self.acao.pk, Coluna.EM_ANDAMENTO, versao_esperada=1)
        self.assertEqual(AcaoReforma.objects.get(pk=self.acao.pk).coluna, Coluna.A_FAZER)

    def test_reforma_concluida_fica_somente_leitura(self):
        self.reforma.situacao = "CONCLUIDA"
        self.reforma.save()
        with self.assertRaises(s.SemPermissao):
            s.registrar_andamento(self.gestor, self.acao.pk, "x")


class PassagemTests(Base):
    def test_passar_adiante_troca_quem_faz_e_registra_o_que_falta(self):
        s.mover_acao(self.gestor, self.acao.pk, Coluna.EM_ANDAMENTO, versao_esperada=1)
        acao = s.passar_adiante(self.gestor, self.acao.pk, s.Passagem(
            feito="Troquei os disjuntores do quadro principal.", o_que_falta="Passar fiação nova até as baias 3 e 4.",
            para_fornecedor=self.pintura), versao_esperada=2)
        self.assertEqual(acao.fornecedor, self.pintura)
        reg = acao.registros.first()
        self.assertEqual((reg.tipo, reg.o_que_falta, reg.passado_para_fornecedor), ("PASSAGEM", "Passar fiação nova até as baias 3 e 4.", self.pintura))

    def test_passagem_exige_texto_e_destino(self):
        for p in (s.Passagem(feito="", o_que_falta="x", para_fornecedor=self.pintura),
                  s.Passagem(feito="x", o_que_falta="x")):
            with self.assertRaises(s.RegraDeNegocio):
                s.passar_adiante(self.gestor, self.acao.pk, p, versao_esperada=1)


class DiarioImutavelTests(Base):
    def test_diario_nao_altera_nem_apaga(self):
        reg = s.registrar_andamento(self.gestor, self.acao.pk, "Comecei a desmontar o forro.")
        with self.assertRaises(PermissionError):
            reg.save()
        with self.assertRaises(PermissionError):
            reg.delete()
        with self.assertRaises(DatabaseError), transaction.atomic():
            RegistroAndamento.objects.filter(pk=reg.pk).update(texto="alterado")
        with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as c:
            c.execute("DELETE FROM reformas_registroandamento WHERE id = %s", [reg.pk])

    def test_texto_vazio_recusado(self):
        with self.assertRaises(s.RegraDeNegocio):
            s.registrar_andamento(self.gestor, self.acao.pk, "   ")


class ChecklistTests(Base):
    def test_marcar_item_guarda_quem_e_quando(self):
        item = ItemChecklist.objects.create(acao=self.acao, texto="Desligar disjuntor geral")
        item = s.marcar_item(self.gestor, item.pk, True)
        self.assertEqual(item.feito_por, self.gestor)
        self.assertIsNotNone(item.feito_em)
        item = s.marcar_item(self.gestor, item.pk, False)
        self.assertIsNone(item.feito_em)
