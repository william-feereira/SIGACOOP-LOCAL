from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.contracts.models import Supplier
from apps.core.access import ADMINISTRADOR, DIRETORIA, GESTOR
from apps.core.models import Unit

from . import servicos as s
from .tests import usuario


class ApiTests(TestCase):
    def setUp(self):
        self.pa = Unit.objects.create(code="PA07", name="PA Jardim")
        self.outro = Unit.objects.create(code="PA08", name="PA Lago")
        self.gestor = usuario("gestor", GESTOR, self.pa)
        self.forn = Supplier.objects.create(name="Elétrica Alfa", document="1", especialidade="Elétrica")
        self.reforma = s.criar_reforma(self.gestor, unidade=self.pa, titulo="Recepção")
        self.acao = s.criar_acao(self.gestor, self.reforma, titulo="Quadro elétrico")
        self.client.force_login(self.gestor)

    def test_sem_login_responde_403_com_link_de_entrada(self):
        self.client.logout()
        r = self.client.get("/api/reformas/")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["codigo"], "nao_autenticado")

    def test_admin_sem_mfa_e_barrado_na_api(self):
        admin = usuario("adm", ADMINISTRADOR)
        TOTPDevice.objects.create(user=admin, name="app", confirmed=True)
        self.client.force_login(admin)
        r = self.client.get("/api/reformas/")
        self.assertEqual((r.status_code, r.json()["codigo"]), (403, "mfa"))

    def test_eu_entrega_perfil_unidades_e_csrf(self):
        r = self.client.get("/api/eu/")
        self.assertEqual(r.json()["perfis"], ["Gestor"])
        self.assertEqual([u["code"] for u in r.json()["unidades"]], ["PA07"])
        self.assertIn("csrftoken", r.cookies)

    def test_criar_reforma_com_acoes_iniciais(self):
        r = self.client.post("/api/reformas/", {"unidade": self.pa.pk, "titulo": "Fachada", "fim_previsto": "2026-12-20",
                                                 "acoes_iniciais": ["Andaime", "Pintura", "  "]}, content_type="application/json")
        self.assertEqual(r.status_code, 201, r.content)
        detalhe = self.client.get(f"/api/reformas/{r.json()['id']}/").json()
        self.assertEqual([a["titulo"] for a in detalhe["acoes"]], ["Andaime", "Pintura"])

    def test_criar_reforma_em_outro_pa_recusado(self):
        r = self.client.post("/api/reformas/", {"unidade": self.outro.pk, "titulo": "X"}, content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_reforma_de_outro_pa_responde_404(self):
        alheio = usuario("alheio", GESTOR, self.outro)
        self.client.force_login(alheio)
        self.assertEqual(self.client.get(f"/api/reformas/{self.reforma.pk}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/acoes/{self.acao.pk}/").status_code, 404)
        r = self.client.post(f"/api/acoes/{self.acao.pk}/mover/", {"coluna": "EM_ANDAMENTO", "versao": 1}, content_type="application/json")
        self.assertEqual(r.status_code, 404)

    def test_fluxo_mover_conflito_bloqueio_passagem(self):
        url = f"/api/acoes/{self.acao.pk}/"
        r = self.client.post(url + "mover/", {"coluna": "EM_ANDAMENTO", "versao": 1}, content_type="application/json")
        self.assertEqual((r.status_code, r.json()["versao"]), (200, 2))
        r = self.client.post(url + "mover/", {"coluna": "VALIDACAO", "versao": 1}, content_type="application/json")
        self.assertEqual((r.status_code, r.json()["codigo"]), (409, "conflito"))
        r = self.client.post(url + "mover/", {"coluna": "BLOQUEADA", "versao": 2}, content_type="application/json")
        self.assertEqual((r.status_code, r.json()["codigo"]), (400, "regra"))
        r = self.client.post(url + "passar/", {"feito": "Troquei disjuntores", "o_que_falta": "Fiação das baias",
                                               "para_fornecedor": self.forn.pk, "versao": 2}, content_type="application/json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["fornecedor"]["nome"], "Elétrica Alfa")
        tipos = [x["tipo"] for x in self.client.get(url).json()["registros"]]
        self.assertEqual(tipos, ["PASSAGEM", "INICIO", "CRIACAO"])

    def test_checklist_e_andamento(self):
        r = self.client.post(f"/api/acoes/{self.acao.pk}/checklist/", {"texto": "Desligar disjuntor"}, content_type="application/json")
        item = r.json()["id"]
        r = self.client.patch(f"/api/checklist/{item}/", {"feito": True}, content_type="application/json")
        self.assertTrue(r.json()["feito"])
        r = self.client.post(f"/api/acoes/{self.acao.pk}/andamento/", {"texto": "Parei no forro da sala 2"}, content_type="application/json")
        self.assertEqual(r.status_code, 201)
        detalhe = self.client.get(f"/api/reformas/{self.reforma.pk}/").json()
        self.assertEqual((detalhe["acoes"][0]["checklist_total"], detalhe["acoes"][0]["checklist_feitos"]), (1, 1))

    def test_diretoria_le_mas_nao_escreve(self):
        self.client.force_login(usuario("dir", DIRETORIA))
        self.assertFalse(self.client.get(f"/api/reformas/{self.reforma.pk}/").json()["pode_editar"])
        r = self.client.post(f"/api/acoes/{self.acao.pk}/andamento/", {"texto": "x"}, content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_csrf_exigido(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.gestor)
        r = c.post(f"/api/acoes/{self.acao.pk}/andamento/", {"texto": "x"}, content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_painel(self):
        s.mover_acao(self.gestor, self.acao.pk, "BLOQUEADA", versao_esperada=1, motivo_bloqueio="Falta material")
        d = self.client.get("/api/painel/").json()
        self.assertEqual((d["reformas_ativas"], d["acoes_bloqueadas"]), (1, 1))

    def test_spa_exige_login(self):
        self.client.logout()
        r = self.client.get("/reformas/1")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/contas/entrar/", r["Location"])
