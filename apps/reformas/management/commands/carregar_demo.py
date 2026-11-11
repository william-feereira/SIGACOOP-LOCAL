"""Cria um cenário de DEMONSTRAÇÃO para conhecer o Kanban de reformas.

Tudo que este comando cria é fictício e marcado como "(demo)" ou "(exemplo)".
Só funciona com config.settings.local (SIGA_PERMITIR_DEMO=True), nunca em produção.
"""
import datetime as dt
import getpass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import UserProfile
from apps.contracts.models import Supplier
from apps.core.models import Unit
from apps.reformas import servicos as s
from apps.reformas.models import Coluna, Reforma

User = get_user_model()


class Command(BaseCommand):
    help = "Cria usuários e uma reforma de demonstração (só para uso local)."

    def add_arguments(self, parser):
        parser.add_argument("--senha", help="Senha dos usuários de demonstração (mínimo 12 caracteres). Sem ela, o comando pergunta.")

    def handle(self, *args, senha=None, **opts):
        if not getattr(settings, "SIGA_PERMITIR_DEMO", False):
            raise CommandError("Demonstração desativada. Use DJANGO_SETTINGS_MODULE=config.settings.local.")
        if Reforma.objects.exists():
            self.stdout.write("Já existem reformas cadastradas. Nada foi alterado.")
            return
        senha = senha or getpass.getpass("Senha para os usuários de demonstração (mín. 12 caracteres): ")
        try:
            validate_password(senha)
        except ValidationError as e:
            raise CommandError(" ".join(e.messages))
        call_command("seed_units", verbosity=0)
        with transaction.atomic():
            self._criar(senha)
        self.stdout.write(self.style.SUCCESS(
            "Demonstração criada. Entre com o usuário 'gestora.demo' (ou 'tecnico.demo') e a senha que você definiu."))

    def _usuario(self, login, nome, sobrenome, perfil, unidade, senha):
        u, _ = User.objects.get_or_create(username=login, defaults={"first_name": nome, "last_name": sobrenome})
        u.set_password(senha)
        u.save()
        u.groups.add(Group.objects.get(name=perfil))
        UserProfile.objects.update_or_create(user=u, defaults={"unit": unidade})
        return u

    def _criar(self, senha):
        hoje = dt.date.today()
        pa = Unit.objects.get(code="PA 01")
        g = self._usuario("gestora.demo", "Gestora", "(demo)", "Gestor", pa, senha)
        tec = self._usuario("tecnico.demo", "Técnico", "TI (demo)", "Solicitante", pa, senha)

        def forn(nome, esp, doc):
            return Supplier.objects.get_or_create(document=doc, defaults={"name": nome, "especialidade": esp})[0]
        fe = forn("Elétrica (exemplo)", "elétrica", "DEMO-0001")
        fp = forn("Pinturas (exemplo)", "pintura", "DEMO-0002")
        fa = forn("Climatização (exemplo)", "ar-condicionado", "DEMO-0003")
        fl = forn("Rede e lógica (exemplo)", "lógica e rede", "DEMO-0004")

        r = s.criar_reforma(g, unidade=pa, titulo="Reforma do salão de atendimento (demo)",
                            objetivo="Cenário fictício para conhecer o quadro.", responsavel=g,
                            inicio=hoje - dt.timedelta(days=20), fim_previsto=hoje + dt.timedelta(days=40))

        def acao(titulo, **k):
            return s.criar_acao(g, r, titulo=titulo, **k)
        proj = acao("Aprovar projeto e layout", responsavel=g, prazo=hoje - dt.timedelta(days=12), prioridade="ALTA")
        demol = acao("Demolição das divisórias antigas", fornecedor=fp, prazo=hoje - dt.timedelta(days=5), depende_de=proj)
        elet = acao("Nova instalação elétrica", fornecedor=fe, prazo=hoje + dt.timedelta(days=6), prioridade="ALTA", depende_de=demol,
                    descricao="Quadro novo, tomadas por posição de atendimento e iluminação LED.")
        logi = acao("Cabeamento de rede e pontos lógicos", fornecedor=fl, prazo=hoje - dt.timedelta(days=1), depende_de=demol)
        ar = acao("Instalar ar-condicionado", fornecedor=fa, prazo=hoje + dt.timedelta(days=15))
        acao("Pintura geral", fornecedor=fp, prazo=hoje + dt.timedelta(days=25), depende_de=elet)
        acao("Rampa e piso tátil (acessibilidade)", prazo=hoje + dt.timedelta(days=30), prioridade="URGENTE")
        acao("Testar equipamentos e liberar o PA", responsavel=tec, prazo=hoje + dt.timedelta(days=38))

        def mover(a, coluna, **k):
            a.refresh_from_db()
            return s.mover_acao(g, a.pk, coluna, versao_esperada=a.versao, **k)
        mover(proj, Coluna.EM_ANDAMENTO); mover(proj, Coluna.CONCLUIDA)
        mover(demol, Coluna.EM_ANDAMENTO)
        s.registrar_andamento(g, demol.pk, "Divisórias do lado esquerdo retiradas. Entulho recolhido.")
        mover(demol, Coluna.CONCLUIDA)
        mover(elet, Coluna.EM_ANDAMENTO)
        for t in ["Passar cabos do salão", "Montar quadro novo", "Instalar tomadas", "Testar circuitos"]:
            s.adicionar_item(g, elet.pk, t)
        for item in list(elet.checklist.all())[:2]:
            s.marcar_item(g, item.pk, True)
        s.registrar_andamento(g, elet.pk, "Quadro montado. Faltam as tomadas das mesas 3 a 6.")
        mover(logi, Coluna.EM_ANDAMENTO)
        mover(logi, Coluna.BLOQUEADA, motivo_bloqueio="Aguardando a operadora liberar o novo ponto de fibra.")
        mover(ar, Coluna.EM_ANDAMENTO)
        ar.refresh_from_db()
        s.passar_adiante(g, ar.pk, s.Passagem("Suportes fixados e tubulação passada.",
                                              "Instalar as evaporadoras e fazer a carga de gás.", None, fa),
                         versao_esperada=ar.versao)
        mover(ar, Coluna.VALIDACAO)
