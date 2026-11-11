from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from apps.accounts.models import AcessoUnidade, UserProfile
from apps.audit.models import AuditEvent
from apps.core.access import ADMINISTRADOR, DIRETORIA, GESTOR, SOLICITANTE, filtrar_por_unidade, pode_gerir_unidade
from apps.core.models import Unit
from apps.requests_center.models import AdministrativeRequest, RequestEvent

User = get_user_model()


def criar_usuario(nome, perfil=None, unidade=None):
    u = User.objects.create_user(nome, password="senha-de-teste-longa")
    if perfil:
        u.groups.add(Group.objects.get(name=perfil))
    if unidade:
        UserProfile.objects.filter(user=u).update(unit=unidade)
    return u


class EscopoPorUnidadeTests(TestCase):
    def setUp(self):
        self.pa1 = Unit.objects.create(code="PA01", name="PA Centro")
        self.pa2 = Unit.objects.create(code="PA02", name="PA Norte")
        self.autor = criar_usuario("autor", SOLICITANTE, self.pa2)
        self.req_pa1 = AdministrativeRequest.objects.create(requester=self.autor, beneficiary_unit=self.pa1, category="OTHER", title="No PA1", description="x", estimated_value=100)
        self.req_pa2 = AdministrativeRequest.objects.create(requester=self.autor, beneficiary_unit=self.pa2, category="OTHER", title="No PA2", description="x", estimated_value=900)

    def url(self, req):
        return f"/solicitacoes/{req.pk}/"

    def test_gestor_ve_so_a_propria_unidade_e_recebe_404_na_outra(self):
        gestor = criar_usuario("gestor", GESTOR, self.pa1)
        self.client.force_login(gestor)
        self.assertEqual(self.client.get(self.url(self.req_pa1)).status_code, 200)
        self.assertEqual(self.client.get(self.url(self.req_pa2)).status_code, 404)
        self.assertEqual(self.client.get("/analytics/").context["total_requests"], 1)

    def test_acesso_extra_a_unidade_amplia_o_escopo(self):
        gestor = criar_usuario("regional", GESTOR, self.pa1)
        AcessoUnidade.objects.create(usuario=gestor, unidade=self.pa2)
        self.client.force_login(gestor)
        self.assertEqual(self.client.get(self.url(self.req_pa2)).status_code, 200)

    def test_solicitante_ve_so_o_que_abriu(self):
        outro = criar_usuario("outro", SOLICITANTE, self.pa1)
        self.client.force_login(outro)
        self.assertEqual(self.client.get(self.url(self.req_pa1)).status_code, 404)
        self.client.force_login(self.autor)
        self.assertEqual(self.client.get(self.url(self.req_pa1)).status_code, 200)

    def test_diretoria_ve_tudo_mas_nao_gere(self):
        diretor = criar_usuario("diretor", DIRETORIA)
        qs = filtrar_por_unidade(AdministrativeRequest.objects.all(), diretor, campo="beneficiary_unit")
        self.assertEqual(qs.count(), 2)
        self.assertFalse(pode_gerir_unidade(diretor, self.pa1.pk))

    def test_usuario_sem_perfil_nao_ve_nada_de_ninguem(self):
        self.client.force_login(criar_usuario("sem_perfil"))
        self.assertEqual(self.client.get("/analytics/").context["total_requests"], 0)
        for url in ("/ativos/", "/frota/", "/contratos/"):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_admin_gere_qualquer_unidade(self):
        admin = criar_usuario("adm", ADMINISTRADOR)
        self.assertTrue(pode_gerir_unidade(admin, self.pa2.pk))


class SolicitacaoTests(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(code="01", name="Sede")
        self.user = criar_usuario("requester", SOLICITANTE, self.unit)
        self.client.force_login(self.user)

    def test_criacao_auditada_e_desfeita_se_auditoria_falhar(self):
        payload = {"beneficiary_unit": self.unit.pk, "category": "OTHER", "title": "New", "description": "Test", "priority": "NORMAL"}
        with patch("apps.requests_center.views.AuditEvent.objects.create", side_effect=RuntimeError("audit failure")):
            with self.assertRaises(RuntimeError):
                self.client.post("/solicitacoes/nova/", payload)
        self.assertFalse(AdministrativeRequest.objects.filter(title="New").exists())
        self.assertFalse(RequestEvent.objects.exists())
        self.assertEqual(self.client.post("/solicitacoes/nova/", payload).status_code, 302)
        self.assertEqual(AuditEvent.objects.get().actor, self.user)

    def test_sair_exige_post(self):
        self.assertContains(self.client.get("/inicio/"), 'method="post"')
        self.assertEqual(self.client.get("/contas/sair/").status_code, 405)

    def test_auditoria_nao_editavel(self):
        from django.contrib.admin import site
        from apps.audit.admin import AuditEventAdmin
        obj = AuditEventAdmin(AuditEvent, site)
        self.assertFalse(obj.has_delete_permission(None))
        self.assertFalse(obj.has_change_permission(None))

    def test_paginas_de_privacidade_publicas(self):
        self.client.logout()
        self.assertContains(self.client.get("/privacidade/"), "privacidade@secovicred.com.br")
        self.assertEqual(self.client.get("/termos/").status_code, 200)

    def test_menu_esconde_modulos_sem_permissao(self):
        html = self.client.get("/inicio/").content.decode()
        self.assertIn('href="/solicitacoes/"', html)
        self.assertNotIn('href="/contratos/"', html)
        self.assertNotIn('href="/admin/"', html)

    def test_cabecalhos_de_seguranca(self):
        r = self.client.get("/inicio/")
        self.assertIn("frame-ancestors 'none'", r["Content-Security-Policy"])
        self.assertEqual(r["X-Frame-Options"], "DENY")


class AppReactTests(TestCase):
    def test_app_exige_login(self):
        r = self.client.get("/reformas")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/contas/entrar/", r["Location"])

    def test_app_recebe_nonce_novo_a_cada_requisicao(self):
        import tempfile
        from pathlib import Path
        from django.test import override_settings
        self.client.force_login(criar_usuario("leitor", GESTOR))
        with tempfile.TemporaryDirectory() as d:
            Path(d, "index.html").write_text('<meta name="csp-nonce" content="__CSP_NONCE__" />', encoding="utf-8")
            with override_settings(SPA_DIR=Path(d)):
                r1, r2 = self.client.get("/reformas"), self.client.get("/reformas")
        self.assertNotIn("__CSP_NONCE__", r1.content.decode())
        csp1, csp2 = r1["Content-Security-Policy"], r2["Content-Security-Policy"]
        self.assertIn("style-src 'self' 'nonce-", csp1)
        self.assertNotIn("unsafe-inline", csp1)
        self.assertNotEqual(csp1, csp2)
        self.assertIn("no-cache", r1["Cache-Control"])
